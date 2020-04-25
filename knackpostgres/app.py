"""
Convert a Knack application to a PostgreSQL Database.
"""
import logging
from pathlib import Path
from pprint import pprint as print
import pdb

from knackpy import get_app_data

from .formula_field import FormulaField
from .constants import TAB
from .table import Table
from .reference_table import ReferenceTable
from .view import View
from .relationship import Relationship
from .utils import valid_pg_name


class App:
    """
    Knack application wrapper. Stores app meta data, tables, fields, etc.
    
    Receives a Knack application ID string and returns App instance.

    On instanciation, will fetch app metadata and prepare output SQL statements.

    Usage:

    >>> `app = App("myappid")`
    >>> app.to_sql()   # write to /sql dir

    """

    def __repr__(self):
        return f"<App {self.name}> ({len(self.objects)} objects)"

    def __init__(self, app_id):

        self.app_id = app_id

        # fetch knack metadata
        self.data = self._get_app_data()

        # assign knack metadata to class attributes
        for key in self.data:
            setattr(self, key, self.data[key])

        self.tables = self._handle_tables()

        self.obj_lookup = self._generate_obj_lookup()

        self._update_one_to_many_relationships()

        self.tables += self._update_many_to_many_relationships()

        self._handle_formulae()

        self.views = self._handle_views()

        logging.info(self)

    # def print_stuff(self):
    #     for obj in self.objects:
    #         for field in obj["fields"]:
    #             if field.get("rules"):
    #                 for rule in field["rules"]:
    #                     print(f"criteria: {rule['criteria']}")
    #                     print(f"values: {rule['values']}")

                # if field["type"] == "equation":
                #     print(field["format"]["equation"])

    def to_sql(self, path="sql"):
        """
        Write application SQL commands to file.

        Alternatively, use the `Loader` class to connect/write directly
        from the `App` class.
        """
        for table in self.tables:
            self._write_sql(table.to_sql(), path, "tables", table.name_postgres)

        for view in self.views:
            self._write_sql(view.sql, path, "views", view.name)

    def _write_sql(self, sql, path, subdir, name_attr, method="w"):

        file_path = Path(path) / subdir

        file_path.mkdir(exist_ok=True, parents=True)

        file_path = file_path / f"{name_attr}.sql"

        with open(file_path, method) as fout:
            fout.write(sql)

    def _get_app_data(self):
        return get_app_data(self.app_id)

    def _handle_tables(self):
        return [Table(obj) for obj in self.objects]

    def _handle_views(self):
        return [View(table) for table in self.tables]

    def _generate_obj_lookup(self):
        """ The obj_lookup allows us to find connected object keys across the entire app """
        return {table.key: table.name_postgres for table in self.tables}

    def _update_one_to_many_relationships(self):
        # sets field definitions for relationship fields,
        # which require references to other tables
        for table in self.tables:
            table.update_one_to_many_relationships(self.obj_lookup)
            # update field map referecnces in table (used by translator)
            table.create_field_map()

    def _update_many_to_many_relationships(self):
        """
        Ah what a joy are many-to-many relationships. to handle these, we need
        to create an associative table which holds relationships across two
        tables. we accomplish this by parsing each relationship definition
        and calling a new `Table` class with the appriate `FieldDef` classes.

        Obviously this all needs to happen after all other tables and fields
        have been instanciated (except for formulae, which rely on relationships)
        so that we can reference the postgres database table and field names.
        """
        fields = self._gather_many_to_many_relationships()

        tables = []

        for field in fields:
            field.set_relationship_references(self)
            
            tables.append(ReferenceTable(field.reference_table_data))
            
        return tables

    def _gather_many_to_many_relationships(self):

        fields = []

        for table in self.tables:
            for field in table.fields:
                try:
                    if field.relationship_type == "many_to_many":
                        fields.append(field)

                except AttributeError:
                    continue
        return fields

    def _handle_formulae(self):
        for table in self.tables:
            for field in table.fields:
                if isinstance(field, FormulaField):
                    field.handle_formula(self)

        return self.tables

    def find_table_from_object_key(self, key, return_attr=None):
        for table in self.tables:
            if table.key == key:
                return table if not return_attr else getattr(table, return_attr)
        return None

    def find_field_from_field_key(self, key, return_attr=None):
        """
        from a knack field key, track down the `FieldDef` instance
        """
        for table in self.tables:
            for field in table.fields:
                if field.key_knack == key:
                    try:
                        return field if not return_attr else getattr(field, return_attr)
                    except AttributeError:
                        return None
        else:
            return None

    def find_table_from_field_key(self, key, return_attr=None):
        """
        from a knack field key, track down the table in which that field lives
        """
        try:
            # some times the connection is under "key", and somtimes it's a string literal
            key = key.get("key")

        except AttributeError:
            pass

        for table in self.tables:
            for field in table.fields:
                if field.key_knack == key:
                    # we found it :)
                    return table if not return_attr else getattr(table, return_attr)

        # no table found that contains this key
        return None
