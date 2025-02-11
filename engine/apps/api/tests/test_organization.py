from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from common.constants.role import Role


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_current_team_retrieve_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    org = make_organization()
    tester = make_user_for_organization(org, role=role)
    _, token = make_token_for_organization(org)

    client = APIClient()

    url = reverse("api-internal:api-current-team")
    with patch(
        "apps.api.views.organization.CurrentOrganizationView.get",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_current_team_update_permissions(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    org = make_organization()
    tester = make_user_for_organization(org, role=role)
    _, token = make_token_for_organization(org)

    client = APIClient()

    url = reverse("api-internal:api-current-team")

    with patch(
        "apps.api.views.organization.CurrentOrganizationView.put",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("feature_flag_enabled", [False, True])
def test_current_team_messaging_backend_status(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    feature_flag_enabled,
):
    org = make_organization()
    tester = make_user_for_organization(org, role=Role.ADMIN)
    _, token = make_token_for_organization(org)

    client = APIClient()

    settings.FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED = feature_flag_enabled
    url = reverse("api-internal:api-current-team")
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["env_status"]["extra_messaging_backends_enabled"] == bool(feature_flag_enabled)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_current_team_get_telegram_verification_code_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)

    client = APIClient()

    url = reverse("api-internal:api-get-telegram-verification-code")
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_current_team_get_channel_verification_code_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(role)

    client = APIClient()

    url = reverse("api-internal:api-get-channel-verification-code") + "?backend=TESTONLY"
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_current_team_get_channel_verification_code_ok(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(Role.ADMIN)

    client = APIClient()

    url = reverse("api-internal:api-get-channel-verification-code") + "?backend=TESTONLY"
    with patch(
        "apps.base.tests.messaging_backend.TestOnlyBackend.generate_channel_verification_code",
        return_value="the-code",
    ) as mock_generate_code:
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "the-code"
    mock_generate_code.assert_called_once_with(organization)


@pytest.mark.django_db
def test_current_team_get_channel_verification_code_invalid(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, tester, token = make_organization_and_user_with_plugin_token(Role.ADMIN)

    client = APIClient()

    url = reverse("api-internal:api-get-channel-verification-code") + "?backend=INVALID"
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
