from pytest import mark

from cap.modules.schemas.models import Schema
from cap.modules.schemas.utils import add_schema_from_fixture


def test_add_or_update_schema_when_schema_does_not_exist_create_new_one(db):  # noqa
    data = dict(name='new-schema',
                version='1.2.3',
                fullname='New fullname',
                deposit_schema={'title': 'deposit_schema'},
                deposit_options={'title': 'deposit_options'},
                record_schema={'title': 'record_schema'},
                record_options={'title': 'record_options'},
                record_mapping={'doc': {'properties': {
                    "title": {"type": "text"}}}},
                deposit_mapping={'doc': {'properties': {
                    "keyword": {"type": "keyword"}}}},
                is_indexed=True,
                use_deposit_as_record=True
                )

    add_schema_from_fixture(data=data)

    schema = Schema.get('new-schema', version='1.2.3')
    for key, value in data.items():
        assert getattr(schema, key) == value


def test_add_or_update_schema_when_schema_already_exist_updates_json_for_schema(db):  # noqa
    updated_data = dict(name='new-schema',
                        version='1.1.1',
                        experiment='LHCb',
                        fullname='New fullname',
                        deposit_schema={'title': 'deposit_schema'},
                        deposit_options={'title': 'deposit_options'},
                        record_schema={'title': 'record_schema'},
                        record_options={'title': 'record_options'},
                        record_mapping={'doc': {'properties': {
                            "title": {"type": "text"}}}},
                        deposit_mapping={'doc': {'properties': {
                            "keyword": {"type": "keyword"}}}},
                        is_indexed=True,
                        use_deposit_as_record=True
                        )
    db.session.add(Schema(**{
        'name': 'new-schema',
        'experiment': 'CMS',
        'fullname': 'Old Schema',
    }))
    db.session.commit()

    add_schema_from_fixture(data=updated_data)

    schema = Schema.get('new-schema', version='1.1.1')
    for key, value in updated_data.items():
        assert getattr(schema, key) == value
