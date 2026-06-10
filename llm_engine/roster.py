"""Источник ростера команды для AssigneeResolverNode.

ЗАГЛУШКА. Реальный ростер должен приходить от бэкенда в context.team_members:
  - из User-таблицы per team (правильный путь, зона Даниила), либо
  - собираться ботом из участников чата (getChatAdministrators / отправители сообщений).
Пока, чтобы пайплайн работал автономно, — известная команда хакатона (§9.6 / demo_data).
"""

from llm_engine.schemas import TeamMember

# TODO: заменить на реальный источник (backend / bot). Сейчас — заглушка.
DEFAULT_TEAM: list[TeamMember] = [
    TeamMember(id="user_daniil", display_name="Даниил", role="captain_backend"),
    TeamMember(id="user_artem", display_name="Артём", role="product_owner_tech_lead"),
    TeamMember(id="user_pavel", display_name="Павел", role="llm_engineer"),
    TeamMember(id="user_ivan", display_name="Иван", role="frontend"),
    TeamMember(id="user_alexey", display_name="Алексей", role="ml"),
]


def default_team() -> list[TeamMember]:
    return list(DEFAULT_TEAM)
