from __future__ import annotations

from odoo_accounting_cli_v4.bridge.runtime import _dispatch


class Record:
    def __init__(self, record_id: int, name: str = "Record") -> None:
        self.id = record_id
        self.name = name


class Records(list):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]


class ReadableModel:
    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return True


class Registry:
    def __init__(self, model_names: set[str]) -> None:
        self.model_names = model_names

    def get(self, model_name: str):
        return object() if model_name in self.model_names else None


class User:
    def has_group(self, xml_id: str) -> bool:
        assert xml_id == "account.group_account_user"
        return True


class CompanyModel(ReadableModel):
    def __init__(self, integrity: dict | None = None) -> None:
        self.integrity = integrity

    def search_count(self, domain, limit=None):
        assert domain == [("id", "=", 7)]
        assert limit == 1
        return 1

    def browse(self, record_id: int):
        assert record_id == 7
        return self

    def _check_hash_integrity(self):
        assert self.integrity is not None
        return self.integrity


class PartnerModel(ReadableModel):
    def search(self, domain):
        assert domain == [
            ("id", "in", [1, 2]),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", 7),
        ]
        return Records([Record(1, "Invoice Partner"), Record(2, "Delivery")])


class AccountModel(ReadableModel):
    def search(self, domain, limit=None):
        assert domain == [("id", "=", 10), ("company_ids", "in", [7])]
        assert limit == 1
        return Record(10, "Source Account")


class TaxModel(ReadableModel):
    def search(self, domain):
        assert domain == [("id", "in", [3, 4]), ("company_id", "=", 7)]
        return Records([Record(3), Record(4)])

    def browse(self, record_ids):
        assert record_ids == [3, 4]
        return Records([Record(3), Record(4)])


class FiscalPosition(Record):
    def map_account(self, account):
        assert account.id == 10
        return Record(11, "Mapped Account")

    def map_tax(self, taxes):
        assert taxes.ids == [3, 4]
        return Records([Record(6, "Mapped Tax")])


class FiscalPositionModel(ReadableModel):
    def with_company(self, company_id: int):
        assert company_id == 7
        return self

    def _get_fiscal_position(self, partner, delivery=None):
        assert partner.id == 1
        assert delivery.id == 2
        return FiscalPosition(5, "Domestic")


class Env:
    uid = 42
    user = User()

    def __init__(self, models: dict[str, object]) -> None:
        self.models = models
        self.registry = Registry(set(models))

    def __getitem__(self, model_name: str):
        return self.models[model_name]


def test_fiscal_position_runtime_uses_odoo_native_resolution_and_mappings() -> None:
    env = Env(
        {
            "res.company": CompanyModel(),
            "res.partner": PartnerModel(),
            "account.fiscal.position": FiscalPositionModel(),
            "account.account": AccountModel(),
            "account.tax": TaxModel(),
        }
    )

    page = _dispatch(
        env,
        "account.fiscal.position.resolve",
        {
            "company_id": 7,
            "partner_id": 1,
            "delivery_partner_id": 2,
            "account_id": 10,
            "tax_ids": [3, 4],
        },
        7,
    )

    assert page == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "data": {
            "company_id": 7,
            "partner_id": 1,
            "delivery_partner_id": 2,
            "fiscal_position": {"id": 5, "name": "Domestic"},
            "account_mapping": {"source_id": 10, "mapped_id": 11},
            "tax_mapping": {"source_ids": [3, 4], "mapped_ids": [6]},
        },
    }


def test_journal_integrity_runtime_returns_the_native_odoo_result() -> None:
    company = CompanyModel(
        {
            "printing_date": "08/25/2026",
            "results": [
                {
                    "journal_name": "Miscellaneous Operations",
                    "restricted_by_hash_table": "X",
                    "status": "no_data",
                    "msg_cover": "No hashed entries.",
                }
            ],
        }
    )
    env = Env(
        {
            "res.company": company,
            "account.journal": ReadableModel(),
            "account.move": ReadableModel(),
        }
    )

    page = _dispatch(
        env,
        "res.company.journal_integrity.inspect",
        {"company_id": 7},
        7,
    )

    assert page["data"] == {
        "company_id": 7,
        "printing_date": "08/25/2026",
        "results": [
            {
                "journal_name": "Miscellaneous Operations",
                "restricted_by_hash_table": "X",
                "status": "no_data",
                "msg_cover": "No hashed entries.",
            }
        ],
    }
    assert page["access_allowed"] is True
