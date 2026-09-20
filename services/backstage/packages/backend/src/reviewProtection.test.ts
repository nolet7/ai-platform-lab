import { enforceReviewProtection } from './reviewProtection';
const policy = () => ({
  enforce_admins: { enabled: true },
  required_pull_request_reviews: { required_approving_review_count: 1, require_code_owner_reviews: true, dismiss_stale_reviews: true, require_last_push_approval: true },
  required_status_checks: { strict: true, contexts: ['application-ci'] },
  required_conversation_resolution: { enabled: true },
  allow_force_pushes: { enabled: false }, allow_deletions: { enabled: false },
});
const response = (status: number, data = {}) => ({ ok: status === 200, status, json: async () => data });
it('fails on unsupported private-repository protection without proceeding', async () => {
  const api = jest.fn().mockResolvedValue(response(403));
  await expect(enforceReviewProtection('secret', 'owner', 'app', 'application-ci', api)).rejects.toThrow('GitHub 403');
  expect(api).toHaveBeenCalledTimes(1);
});
it('enforces reviews for administrators and verifies the saved policy', async () => {
  const api = jest.fn().mockResolvedValueOnce(response(200)).mockResolvedValueOnce(response(200, policy()));
  await enforceReviewProtection('secret', 'owner', 'app', 'application-ci', api);
  const body = JSON.parse(api.mock.calls[0][1].body);
  expect(body.enforce_admins).toBe(true);
  expect(body.required_pull_request_reviews.require_last_push_approval).toBe(true);
  expect(api).toHaveBeenCalledTimes(2);
});
it.each(['enforce_admins', 'required_pull_request_reviews', 'required_status_checks', 'required_conversation_resolution', 'allow_force_pushes', 'allow_deletions'])('rejects a policy missing %s', async field => {
  const current: any = policy(); delete current[field];
  const api = jest.fn().mockResolvedValueOnce(response(200)).mockResolvedValueOnce(response(200, current));
  await expect(enforceReviewProtection('secret', 'owner', 'app', 'application-ci', api)).rejects.toThrow('verification failed');
});
it('rejects an unexpected CI context', async () => {
  const current = policy(); current.required_status_checks.contexts = ['unrelated'];
  const api = jest.fn().mockResolvedValueOnce(response(200)).mockResolvedValueOnce(response(200, current));
  await expect(enforceReviewProtection('secret', 'owner', 'app', 'application-ci', api)).rejects.toThrow('verification failed');
});
it('rejects path injection before sending credentials', async () => {
  const api = jest.fn();
  await expect(enforceReviewProtection('secret', '../other', 'app', 'application-ci', api)).rejects.toThrow('Invalid');
  expect(api).not.toHaveBeenCalled();
});
