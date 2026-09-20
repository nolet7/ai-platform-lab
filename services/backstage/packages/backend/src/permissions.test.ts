import { ProjectPolicy } from './permissions';
import { AuthorizeResult, createPermission } from '@backstage/plugin-permission-common';
const policy = new ProjectPolicy();
const user = (groups: string[]) => ({ info: { userEntityRef: 'user:default/demo-requester', ownershipEntityRefs: groups } } as any);
const request = (name: string) => ({ permission: createPermission({ name, attributes: {} }) });
it('requires authenticated ML team membership to create a project', async () => {
  expect((await policy.handle(request('scaffolder.task.create'))).result).toBe(AuthorizeResult.DENY);
  expect((await policy.handle(request('scaffolder.task.create'), user([]))).result).toBe(AuthorizeResult.DENY);
  expect((await policy.handle(request('scaffolder.task.create'), user(['group:default/tax-ml-team']))).result).toBe(AuthorizeResult.ALLOW);
});
it.each(['catalog.entity.delete', 'scaffolder.template.management', 'scaffolder.template.dryRun'])('prevents model users from injecting templates through %s', async name => {
  expect((await policy.handle(request(name), user(['group:default/tax-ml-team']))).result).toBe(AuthorizeResult.DENY);
});

it('permits ML project registration but not for non-members', async () => {
  expect((await policy.handle(request('catalog.location.create'), user([]))).result).toBe(AuthorizeResult.DENY);
  expect((await policy.handle(request('catalog.location.create'), user(['group:default/tax-ml-team']))).result).toBe(AuthorizeResult.ALLOW);
});

it('permits developers to request and register applications but not manage templates', async () => {
  const developer = user(['group:default/developers']);
  for (const name of ['scaffolder.task.create', 'catalog.entity.create', 'catalog.location.create']) {
    expect((await policy.handle(request(name), developer)).result).toBe(AuthorizeResult.ALLOW);
  }
  expect((await policy.handle(request('scaffolder.template.management'), developer)).result).toBe(AuthorizeResult.DENY);
});
