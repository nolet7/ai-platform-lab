import { coreServices, createBackendModule } from '@backstage/backend-plugin-api';
import { createTemplateAction, scaffolderActionsExtensionPoint } from '@backstage/plugin-scaffolder-node';

const identifier = /^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/;
export async function enforceReviewProtection(
  token: string, owner: string, repo: string, check: string,
  request: typeof fetch = fetch,
): Promise<void> {
  if (!identifier.test(owner) || !identifier.test(repo) || !['application-ci', 'deployment-ci'].includes(check)) {
    throw new Error('Invalid protected repository or required check');
  }
  const endpoint = `https://api.github.com/repos/${owner}/${repo}/branches/main/protection`;
  const headers = { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json' };
  const policy = {
    required_status_checks: { strict: true, contexts: [check] },
    enforce_admins: true,
    required_pull_request_reviews: {
      required_approving_review_count: 1, require_code_owner_reviews: true,
      dismiss_stale_reviews: true, require_last_push_approval: true,
    },
    restrictions: null, required_conversation_resolution: true,
    allow_force_pushes: false, allow_deletions: false,
  };
  const response = await request(endpoint, { method: 'PUT', headers, body: JSON.stringify(policy), signal: AbortSignal.timeout(30000) });
  if (!response.ok) {
    throw new Error(`Review protection could not be enabled for ${owner}/${repo} (GitHub ${response.status}). Check private-repository plan support and Administration permission. Only bootstrap metadata may exist; no application code is published by this failed request.`);
  }
  // The standard publisher treats the unsupported-plan response as a warning.
  // Read back GitHub's policy and fail the task if any required guarantee is missing.
  const verified = await request(endpoint, { headers, signal: AbortSignal.timeout(30000) });
  if (!verified.ok) throw new Error(`Cannot verify review protection for ${owner}/${repo} (GitHub ${verified.status})`);
  const current = await verified.json();
  const reviews = current.required_pull_request_reviews;
  if (!current.enforce_admins?.enabled || !reviews || reviews.required_approving_review_count < 1 ||
      !reviews.require_code_owner_reviews || !reviews.dismiss_stale_reviews || !reviews.require_last_push_approval ||
      !current.required_status_checks?.strict || !current.required_status_checks?.contexts?.includes(check) ||
      !current.required_conversation_resolution?.enabled || current.allow_force_pushes?.enabled !== false ||
      current.allow_deletions?.enabled !== false) {
    throw new Error(`Review protection verification failed for ${owner}/${repo}; request stopped before publishing application code`);
  }
}

export const reviewProtectionModule = createBackendModule({
  pluginId: 'scaffolder', moduleId: 'required-review-protection',
  register(reg) {
    reg.registerInit({ deps: { actions: scaffolderActionsExtensionPoint, config: coreServices.rootConfig },
      async init({ actions, config }) {
        const integration = config.getConfigArray('integrations.github').find(item => item.getString('host') === 'github.com');
        actions.addActions(createTemplateAction({
          id: 'platform:github:require-review',
          description: 'Enable and verify mandatory review and CI protection; fail closed on unsupported GitHub plans.',
          schema: { input: {
            owner: z => z.string().regex(identifier), repo: z => z.string().regex(identifier),
            check: z => z.enum(['application-ci', 'deployment-ci']),
          } },
          async handler(ctx) {
            if (!integration) throw new Error('GitHub integration is not configured');
            await enforceReviewProtection(integration.getString('token'), ctx.input.owner, ctx.input.repo, ctx.input.check);
            ctx.logger.info(`Verified mandatory review protection for ${ctx.input.owner}/${ctx.input.repo}`);
          },
        }));
      },
    });
  },
});
