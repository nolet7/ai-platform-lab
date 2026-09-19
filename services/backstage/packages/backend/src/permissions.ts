import { createBackendModule } from '@backstage/backend-plugin-api';
import { policyExtensionPoint } from '@backstage/plugin-permission-node/alpha';
import { AuthorizeResult, PolicyDecision } from '@backstage/plugin-permission-common';
import { PermissionPolicy, PolicyQuery, PolicyQueryUser } from '@backstage/plugin-permission-node';

export class ProjectPolicy implements PermissionPolicy {
  async handle(request: PolicyQuery, user?: PolicyQueryUser): Promise<PolicyDecision> {
    const groups = user?.info.ownershipEntityRefs ?? [];
    if (!user) return { result: AuthorizeResult.DENY };
    if (groups.includes('group:default/platform-team')) return { result: AuthorizeResult.ALLOW };
    // Template management and deletion remain restricted. Global catalog rules
    // permit Component imports but reject Template/User/Group from dynamic locations.
    if (request.permission.name === 'scaffolder.template.management' ||
        request.permission.name === 'scaffolder.template.dryRun' ||
        request.permission.name === 'catalog.entity.delete' ||
        request.permission.name === 'catalog.location.delete') {
      return { result: AuthorizeResult.DENY };
    }
    if (request.permission.name === 'scaffolder.task.create' || request.permission.name === 'catalog.location.create' || request.permission.name === 'catalog.entity.create') {
      return { result: groups.includes('group:default/tax-ml-team') ? AuthorizeResult.ALLOW : AuthorizeResult.DENY };
    }
    return { result: AuthorizeResult.ALLOW };
  }
}
export const permissionModule = createBackendModule({
  pluginId: 'permission', moduleId: 'project-policy',
  register(reg) {
    reg.registerInit({ deps: { policy: policyExtensionPoint }, async init({ policy }) {
      policy.setPolicy(new ProjectPolicy());
    }});
  },
});
