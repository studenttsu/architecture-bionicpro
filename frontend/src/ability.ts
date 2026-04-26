import { AbilityBuilder, createMongoAbility, MongoAbility } from '@casl/ability';

type Actions = 'view';
type Subjects = 'Report';

export type AppAbility = MongoAbility<[Actions, Subjects]>;

export function defineAbilityFor(roles: string[]): AppAbility {
  const { can, build } = new AbilityBuilder<AppAbility>(createMongoAbility);

  if (roles.includes('prothetic_user')) {
    can('view', 'Report');
  }

  return build();
}
