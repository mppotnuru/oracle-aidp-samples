from __future__ import annotations

import importlib.util
import os
import unittest

from aws_aidp.translate.athena_to_spark_sql import translate
from aws_aidp.translate.glue_to_spark import translate as translate_glue
from tests.stress.helpers import load_fixture


HAS_PYSPARK = importlib.util.find_spec("pyspark") is not None


@unittest.skipUnless(HAS_PYSPARK, "install pyspark to enable Spark parser checks")
class SparkRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pyspark.sql import SparkSession

        cls.spark = SparkSession.builder.master("local[1]").appName(
            "aws-aidp-stress"
        ).getOrCreate()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_runtime_version_matches_pin_when_configured(self):
        expected = os.environ.get("AIDP_SPARK_VERSION")
        if not expected:
            self.skipTest("set AIDP_SPARK_VERSION to enforce the target runtime")
        self.assertTrue(self.spark.version.startswith(expected))

    def test_every_zero_flag_fixture_query_parses(self):
        parser = self.spark._jsparkSession.sessionState().sqlParser()
        queries = load_fixture()["sources"]["athena"]["items"]["named_queries"]
        for query in queries:
            result = translate(query["query"])
            if result.flags:
                continue
            with self.subTest(query=query["name"]):
                parser.parsePlan(result.translated_sql)

    def test_glue_catalog_identifier_with_hyphens_parses_per_part(self):
        source = (
            'frame = ctx.create_dynamic_frame.from_catalog('
            'database="raw-zone", table_name="claims-2026")\n'
        )
        result = translate_glue(source, oci_namespace="ns")
        self.assertIn('spark.table("`raw-zone`.`claims-2026`")', result.translated_sql)
        parser = self.spark._jsparkSession.sessionState().sqlParser()
        identifiers = parser.parseMultipartIdentifier("`raw-zone`.`claims-2026`")
        self.assertEqual(
            [identifiers.apply(index) for index in range(identifiers.size())],
            ["raw-zone", "claims-2026"],
        )

    def test_supported_scalar_rewrites_execute(self):
        cases = [
            (
                "SELECT JSON_EXTRACT_SCALAR('{\"score\":7}', '$.score') AS value",
                "7",
            ),
            (
                "SELECT date_format(to_timestamp('2026-09-09 12:00:00'), '%Y-%m-%d') AS value",
                "2026-09-09",
            ),
            (
                "SELECT strpos('alphabet', 'pha') AS value",
                3,
            ),
            (
                # Character classes keep this a zero-flag case; backslash escapes
                # are covered by test_regex_escape_hazard_is_observable_in_spark.
                "SELECT regexp_extract('100-200', '([0-9]+)-([0-9]+)', 0) AS value",
                "100-200",
            ),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result = translate(source)
                self.assertEqual(result.flags, 0, [str(f) for f in result.findings])
                actual = self.spark.sql(result.translated_sql).first()["value"]
                self.assertEqual(actual, expected)

        zip_result = translate(
            "SELECT zip(array(1, 2), array('a', 'b')) AS value"
        )
        self.assertEqual(zip_result.flags, 0, [str(f) for f in zip_result.findings])
        self.assertEqual(
            len(self.spark.sql(zip_result.translated_sql).first()["value"]),
            2,
        )

    def test_regex_escape_hazard_is_observable_in_spark(self):
        # Athena reads '(\d+)' as the regex \d+; Spark's default parser consumes
        # the backslash first, so the same literal no longer matches digits.
        result = translate(r"SELECT regexp_extract('100-200', '(\d+)-(\d+)', 1) AS value")
        self.assertEqual(
            [finding.rule for finding in result.findings],
            ["regex_escape_sequence"],
        )
        self.assertNotEqual(
            self.spark.sql(result.translated_sql).first()["value"],
            "100",
        )

    def test_double_quoted_identifier_rewrite_parses(self):
        result = translate('SELECT "id" FROM "acme-db"."claims"')
        self.assertEqual(result.translated_sql, "SELECT `id` FROM `acme-db`.`claims`")
        self.assertEqual(result.flags, 0)
        parser = self.spark._jsparkSession.sessionState().sqlParser()
        parser.parsePlan(result.translated_sql)

    def test_flagged_string_dialect_differences_are_observable_in_spark(self):
        split_result = translate("SELECT split('a,b', ',')[1] AS value")
        self.assertEqual(
            [finding.rule for finding in split_result.findings],
            ["split_subscript_index"],
        )
        self.assertEqual(
            self.spark.sql(split_result.translated_sql).first()["value"],
            "b",
        )

        regexp_result = translate(
            "SELECT regexp_extract('100-200', '([0-9]+)-([0-9]+)') AS value"
        )
        self.assertEqual(
            [finding.rule for finding in regexp_result.findings],
            ["regexp_extract_default_group"],
        )
        self.assertEqual(
            self.spark.sql(regexp_result.translated_sql).first()["value"],
            "100",
        )

        cast_result = translate("SELECT CAST(1 AS VARCHAR) AS value")
        self.assertEqual(
            [finding.rule for finding in cast_result.findings],
            ["cast_varchar"],
        )
        parser = self.spark._jsparkSession.sessionState().sqlParser()
        with self.assertRaisesRegex(Exception, "DATATYPE_MISSING_SIZE"):
            parser.parsePlan(cast_result.translated_sql)

    def test_cardinality_null_contract_under_ansi_mode(self):
        result = translate("SELECT cardinality(CAST(NULL AS ARRAY<INT>)) AS value")
        self.assertTrue(any(
            finding.rule == "cardinality_null_semantics"
            for finding in result.findings
        ))
        previous = self.spark.conf.get("spark.sql.ansi.enabled")
        try:
            self.spark.conf.set("spark.sql.ansi.enabled", "true")
            self.assertIsNone(self.spark.sql(result.translated_sql).first()["value"])
            non_null = translate("SELECT cardinality(array(1, 2)) AS value")
            self.assertTrue(any(
                finding.rule == "cardinality_null_semantics"
                for finding in non_null.findings
            ))
            self.assertEqual(
                self.spark.sql(non_null.translated_sql).first()["value"],
                2,
            )
        finally:
            self.spark.conf.set("spark.sql.ansi.enabled", previous)

    def test_array_agg_null_difference_is_visible(self):
        source = (
            "SELECT array_agg(value) AS values FROM VALUES "
            "(CAST(1 AS INT)), (CAST(NULL AS INT)), (CAST(2 AS INT)) AS t(value)"
        )
        result = translate(source)
        self.assertTrue(any(
            finding.rule == "array_agg_semantics" for finding in result.findings
        ))
        self.assertEqual(self.spark.sql(result.translated_sql).first()["values"], [1, 2])

    def test_pinned_compatible_constructs_execute(self):
        cast_result = translate("SELECT try_cast('not-a-number' AS DOUBLE) AS value")
        self.assertEqual(cast_result.flags, 0)
        self.assertIsNone(self.spark.sql(cast_result.translated_sql).first()["value"])

        aggregate_result = translate(
            "SELECT max_by(value, ordering) AS max_value, "
            "min_by(value, ordering) AS min_value "
            "FROM VALUES ('low', 1), ('high', 2) AS t(value, ordering)"
        )
        self.assertEqual(aggregate_result.flags, 0)
        row = self.spark.sql(aggregate_result.translated_sql).first()
        self.assertEqual((row["max_value"], row["min_value"]), ("high", "low"))

    def test_simple_unnest_rewrite_executes(self):
        source = (
            "SELECT value FROM (SELECT array(1, 2, 3) AS values) t "
            "CROSS JOIN UNNEST(values) AS u(value)"
        )
        result = translate(source)
        self.assertEqual(result.flags, 0)
        rows = [row["value"] for row in self.spark.sql(result.translated_sql).collect()]
        self.assertEqual(rows, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
