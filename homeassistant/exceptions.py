"""The exceptions used by Home Assistant."""
from __future__ import annotations

from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING

import attr

if TYPE_CHECKING:
    from .core import Context


class HomeAssistantError(Exception):
    """General Home Assistant exception occurred."""


class InvalidEntityFormatError(HomeAssistantError):
    """When an invalid formatted entity is encountered."""


class NoEntitySpecifiedError(HomeAssistantError):
    """When no entity is specified."""


class TemplateError(HomeAssistantError):
    """Error during template rendering."""

    def __init__(self, exception: Exception | str) -> None:
        """Init the error."""
        if isinstance(exception, str):
            super().__init__(exception)
        else:
            super().__init__(f"{exception.__class__.__name__}: {exception}")


@attr.s
class ConditionError(HomeAssistantError):
    """Error during condition evaluation."""

    # The type of the failed condition, such as 'and' or 'numeric_state'
    type: str = attr.ib()

    @staticmethod
    def _indent(indent: int, message: str) -> str:
        """Return indentation."""
        return "  " * indent + message

    def output(self, indent: int) -> Generator[str, None, None]:
        """Yield an indented representation."""
        raise NotImplementedError()

    def __str__(self) -> str:
        """Return string representation."""
        return "\n".join(list(self.output(indent=0)))


@attr.s
class ConditionErrorMessage(ConditionError):
    """Condition error message."""

    # A message describing this error
    message: str = attr.ib()

    def output(self, indent: int) -> Generator[str, None, None]:
        """Yield an indented representation."""
        yield self._indent(indent, f"In '{self.type}' condition: {self.message}")


@attr.s
class ConditionErrorIndex(ConditionError):
    """Condition error with index."""

    # The zero-based index of the failed condition, for conditions with multiple parts
    index: int = attr.ib()
    # The total number of parts in this condition, including non-failed parts
    total: int = attr.ib()
    # The error that this error wraps
    error: ConditionError = attr.ib()

    def output(self, indent: int) -> Generator[str, None, None]:
        """Yield an indented representation."""
        if self.total > 1:
            yield self._indent(
                indent, f"In '{self.type}' (item {self.index+1} of {self.total}):"
            )
        else:
            yield self._indent(indent, f"In '{self.type}':")

        yield from self.error.output(indent + 1)


@attr.s
class ConditionErrorContainer(ConditionError):
    """Condition error with subconditions."""

    # List of ConditionErrors that this error wraps
    errors: Sequence[ConditionError] = attr.ib()

    def output(self, indent: int) -> Generator[str, None, None]:
        """Yield an indented representation."""
        for item in self.errors:
            yield from item.output(indent)


class IntegrationError(HomeAssistantError):
    """Base class for platform and config entry exceptions."""

    def __str__(self) -> str:
        """Return a human readable error."""
        return super().__str__() or str(self.__cause__)


class PlatformNotReady(IntegrationError):
    """Error to indicate that platform is not ready."""


class ConfigEntryNotReady(IntegrationError):
    """Error to indicate that config entry is not ready."""


class ConfigEntryAuthFailed(IntegrationError):
    """Error to indicate that config entry could not authenticate."""


class InvalidStateError(HomeAssistantError):
    """When an invalid state is encountered."""


class Unauthorized(HomeAssistantError):
    """When an action is unauthorized."""

    def __init__(
        self,
        context: Context | None = None,
        user_id: str | None = None,
        entity_id: str | None = None,
        config_entry_id: str | None = None,
        perm_category: str | None = None,
        permission: str | None = None,
    ) -> None:
        """Unauthorized error."""
        super().__init__(self.__class__.__name__)
        self.context = context

        if user_id is None and context is not None:
            user_id = context.user_id

        self.user_id = user_id
        self.entity_id = entity_id
        self.config_entry_id = config_entry_id
        # Not all actions have an ID (like adding config entry)
        # We then use this fallback to know what category was unauth
        self.perm_category = perm_category
        self.permission = permission


class UnknownUser(Unauthorized):
    """When call is made with user ID that doesn't exist."""


class ServiceNotFound(HomeAssistantError):
    """Raised when a service is not found."""

    def __init__(self, domain: str, service: str) -> None:
        """Initialize error."""
        super().__init__(self, f"Service {domain}.{service} not found")
        self.domain = domain
        self.service = service

    def __str__(self) -> str:
        """Return string representation."""
        return f"Unable to find service {self.domain}.{self.service}"


class MaxLengthExceeded(HomeAssistantError):
    """Raised when a property value has exceeded the max character length."""

    def __init__(self, value: str, property_name: str, max_length: int) -> None:
        """Initialize error."""
        super().__init__(
            self,
            (
                f"Value {value} for property {property_name} has a max length of "
                f"{max_length} characters"
            ),
        )
        self.value = value
        self.property_name = property_name
        self.max_length = max_length


class RequiredParameterMissing(HomeAssistantError):
    """Raised when a required parameter is missing from a function call."""

    def __init__(self, parameter_names: list[str]) -> None:
        """Initialize error."""
        super().__init__(
            self,
            (
                "Call must include at least one of the following parameters: "
                f"{', '.join(parameter_names)}"
            ),
        )
        self.parameter_names = parameter_names


class DependencyError(HomeAssistantError):
    """Raised when dependencies can not be setup."""

    def __init__(self, failed_dependencies: list[str]) -> None:
        """Initialize error."""
        super().__init__(
            self,
            f"Could not setup dependencies: {', '.join(failed_dependencies)}",
        )
        self.failed_dependencies = failed_dependencies
