import { createBackendModule } from '@backstage/backend-plugin-api';
import { authProvidersExtensionPoint, createOAuthProviderFactory } from '@backstage/plugin-auth-node';
import { oidcAuthenticator } from '@backstage/plugin-auth-backend-module-oidc-provider';
export const oidcModule = createBackendModule({
  pluginId: 'auth', moduleId: 'keycloak',
  register(reg) {
    reg.registerInit({
      deps: { providers: authProvidersExtensionPoint },
      async init({ providers }) {
        providers.registerProvider({
          providerId: 'oidc',
          factory: createOAuthProviderFactory({
            authenticator: oidcAuthenticator,
            async signInResolver(info, ctx) {
              const name = info.result.fullProfile.userinfo.preferred_username;
              if (typeof name !== 'string' || !/^[a-z0-9-]+$/.test(name)) {
                throw new Error('A recognized Keycloak username is required');
              }
              return ctx.signInWithCatalogUser({ entityRef: { name } });
            },
          }),
        });
      },
    });
  },
});
