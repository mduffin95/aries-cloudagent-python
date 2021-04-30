"""Validator methods to check for properties without a context."""

from typing import Sequence, Tuple, Union
from pyld import jsonld


from .document_loader import DocumentLoaderMethod


def diff_dict_keys(full: dict, with_missing: dict, prefix: str = None) -> Sequence[str]:
    """Get the difference in dict keys between full and with_missing.

    Checks recursively

    Args:
        full (dict): The full dict with all keys present
        with_missing (dict): The dict with possibly keys missing
        prefix (str, optional): The prefix. Mostly used for internal recursion.

    Returns:
        Sequence[str]: List of missing property names in with_missing

    """

    def _normalize(
        full: Union[dict, list], with_missing: Union[dict, list]
    ) -> Tuple[Union[dict, list], Union[dict, list]]:
        full_type = type(full)
        with_missing_type = type(with_missing)

        if full_type == with_missing_type:
            return (full, with_missing)

        # First type is a list. Return first item if len is 1
        if full_type == list and with_missing_type != list:
            return (full, [with_missing])

    missing = []

    # Loop trough all key/value pairs of the full document
    for key, value in full.items():

        # skip json-ld keywords
        if jsonld._is_keyword(key):
            continue

        _prefix = f"{prefix}.{key}" if prefix else key
        # If the key is not present in the with_missing dict, add it to the list
        if key not in with_missing:
            missing.append(_prefix)

        # If the key is present, but is a dict itself, recursively check nested keys
        elif isinstance(value, dict):
            missing.extend(diff_dict_keys(value, with_missing.get(key), prefix=_prefix))

        # If the key is present, but is a list, recursively check nested keys for entries
        elif isinstance(value, list):
            value, value_with_missing = _normalize(value, with_missing.get(key))

            for i in range(len(value)):
                nested_value = value[i]

                # Only check for nested list or dict. We're not checking for string values
                if isinstance(nested_value, (dict, list)):
                    __prefix = f"{_prefix}[{i}]"

                    nested_value, nested_with_missing = _normalize(
                        nested_value, value_with_missing[i]
                    )
                    missing.extend(
                        diff_dict_keys(
                            nested_value, nested_with_missing, prefix=__prefix
                        )
                    )

    return missing


# FIXME: It seems like there is a bug in pyld with scoped contexts
# that gives incorrect and inconsistent output. This is caused by other
# pyld operations in ACA-Py. Therefore it is not possible to check for dropped properties
# at the moment.
# See: https://github.com/digitalbazaar/pyld/issues/123
def get_properties_without_context(
    document: dict, document_loader: DocumentLoaderMethod
) -> Sequence[str]:
    """Get the properties from document that don't have an context definition."""
    # FIXME: this doesn't work with nested @context structures...
    if "verifiableCredential" in document:
        return []

    document = document.copy()

    # Removes unknown keys from object
    compact = jsonld.compact(
        document,
        document["@context"],
        {"documentLoader": document_loader},
    )

    missing = diff_dict_keys(document, compact)

    return missing