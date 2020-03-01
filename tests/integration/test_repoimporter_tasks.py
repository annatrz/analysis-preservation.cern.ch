import tarfile

from invenio_files_rest.models import ObjectVersion

import responses
from cap.modules.git.errors import GitObjectNotFound
from cap.modules.git.models import GitWebhookSubscriber
from cap.modules.git.tasks import (download_repo, download_repo_file,
                                   ping_webhooks)
from mock import Mock, patch


@patch('cap.modules.git.factory.GithubAPI')
@patch('cap.modules.git.factory.GitlabAPI')
def test_ping_webhooks_when_webhook_exist_status_stays_active(
        m_gitlab, m_github, gitlab_push_webhook_sub, github_push_webhook_sub,
        superuser):
    m_gitlab_ping = Mock(return_value=None)
    m_github_ping = Mock(return_value=None)
    m_gitlab.return_value = Mock(ping_webhook=m_gitlab_ping)
    m_github.return_value = Mock(ping_webhook=m_github_ping)

    assert github_push_webhook_sub.status == 'active'
    assert gitlab_push_webhook_sub.status == 'active'

    ping_webhooks.delay()

    m_github.assert_called_with('github.com', 'owner', 'repository',
                                'mybranch', superuser.id)
    m_gitlab.assert_called_with('gitlab.cern.ch', 'owner_name', 'myrepository',
                                'mybranch', superuser.id)
    m_github_ping.assert_called_with(
        github_push_webhook_sub.webhook.external_id)
    m_gitlab_ping.assert_called_with(
        gitlab_push_webhook_sub.webhook.external_id)

    assert GitWebhookSubscriber.query.get(
        github_push_webhook_sub.id).status == 'active'
    assert GitWebhookSubscriber.query.get(
        gitlab_push_webhook_sub.id).status == 'active'


@patch('cap.modules.git.factory.GithubAPI')
@patch('cap.modules.git.factory.GitlabAPI')
def test_ping_webhooks_when_webhook_doesnt_exists_change_subscriber_status_to_deleted(
        m_gitlab, m_github, gitlab_push_webhook_sub, github_push_webhook_sub,
        superuser):
    m_gitlab_ping = Mock(side_effect=GitObjectNotFound)
    m_github_ping = Mock(side_effect=GitObjectNotFound)
    m_gitlab.return_value = Mock(ping_webhook=m_gitlab_ping)
    m_github.return_value = Mock(ping_webhook=m_github_ping)

    assert github_push_webhook_sub.status == 'active'
    assert gitlab_push_webhook_sub.status == 'active'

    ping_webhooks.delay()

    m_github.assert_called_with('github.com', 'owner', 'repository',
                                'mybranch', superuser.id)
    m_gitlab.assert_called_with('gitlab.cern.ch', 'owner_name', 'myrepository',
                                'mybranch', superuser.id)

    assert GitWebhookSubscriber.query.get(
        github_push_webhook_sub.id).status == 'deleted'
    assert GitWebhookSubscriber.query.get(
        gitlab_push_webhook_sub.id).status == 'deleted'


@responses.activate
def test_download_repo_file(deposit, file_tar):
    responses.add(
        responses.GET,
        'https://raw.githubusercontent.com/owner/repository/mybranchsha/README.md',  # noqa
        body=file_tar,
        content_type='text/plain',
        headers={
            'Content-Length': '18',
            'Content-Encoding': 'gzip',
            'Content-Type': 'text/plain; charset=utf-8'
        },
        stream=True,
        status=200)

    download_repo_file(
        deposit.id,
        'repositories/github.com/owner/repository/mybranch/README.md',
        'https://raw.githubusercontent.com/owner/repository/mybranchsha/README.md',  # noqa
        {'Authorization': 'token mysecretsecret'},
    )

    assert responses.calls[0].request.headers[
        'Authorization'] == 'token mysecretsecret'

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/github.com/owner/repository/mybranch/README.md')
    open_file = open(obj.file.uri)
    repo_content = open_file.read()
    assert repo_content == 'test repo for cap\n'


@responses.activate
def test_download_repo_file_when_failed_creates_empty_file_object_with_failed_tag(
        deposit, file_tar):
    responses.add(
        responses.GET,
        'https://raw.githubusercontent.com/owner/repository/mybranchsha/README.md',  # noqa
        body=file_tar,
        content_type='text/plain',
        headers={
            'Content-Length': '18',
            'Content-Encoding': 'gzip',
            'Content-Type': 'text/plain; charset=utf-8'
        },
        stream=True,
        status=400)

    download_repo_file(
        deposit.id,
        'repositories/github.com/owner/repository/mybranch/README.md',
        'https://raw.githubusercontent.com/owner/repository/mybranchsha/README.md',  # noqa
        {'Authorization': 'token mysecretsecret'},
    )

    assert responses.calls[0].request.headers[
        'Authorization'] == 'token mysecretsecret'

    # file object was created
    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/github.com/owner/repository/mybranch/README.md')

    # but tagged as failed
    tag = obj.tags[0]
    assert tag.key, tag.value == ('status', 'failed')


@responses.activate
def test_download_repo(deposit, git_repo_tar):
    responses.add(
        responses.GET,
        'https://codeload.github.com/owner/repository/legacy.tar.gz/mybranchsha',
        body=git_repo_tar,
        content_type='application/x-gzip',
        headers={
            'Transfer-Encoding': 'chunked',
            'Content-Length': '287'
        },
        stream=True,
        status=200)

    download_repo(
        deposit.id,
        'repositories/github.com/owner/repository/mybranch.tar.gz',
        'https://codeload.github.com/owner/repository/legacy.tar.gz/mybranchsha',  # noqa
        {'Authorization': 'token mysecretsecret'},
    )

    assert responses.calls[0].request.headers[
        'Authorization'] == 'token mysecretsecret'

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/github.com/owner/repository/mybranch.tar.gz')
    tar_obj = tarfile.open(obj.file.uri)
    repo_file_name = tar_obj.getmembers()[1]
    repo_content = tar_obj.extractfile(repo_file_name).read()

    assert repo_content == b'test repo for cap\n'


@responses.activate
def test_download_repo_when_failed_creates_empty_file_object_with_failed_tag(
        deposit, git_repo_tar):
    responses.add(
        responses.GET,
        'https://codeload.github.com/owner/repository/legacy.tar.gz/mybranchsha',  # noqa
        body=git_repo_tar,
        content_type='application/x-gzip',
        headers={
            'Transfer-Encoding': 'chunked',
            'Content-Length': '287'
        },
        stream=True,
        status=400)

    download_repo(
        deposit.id,
        'repositories/github.com/owner/repository/mybranch.tar.gz',
        'https://codeload.github.com/owner/repository/legacy.tar.gz/mybranchsha',  # noqa
        {'Authorization': 'token mysecretsecret'},
    )

    # file object was created
    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/github.com/owner/repository/mybranch.tar.gz')

    # but tagged as failed
    tag = obj.tags[0]
    assert tag.key, tag.value == ('status', 'failed')
