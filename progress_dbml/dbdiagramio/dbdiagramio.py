class DB_Diagram_IO:
    def __init__(self, save_path):
        self.save_path = save_path

    def makeStrSafe(self, str_to_escape):
        return '"' + str_to_escape + '"'

    def buildFieldOptions(self, pg_field):
        options = []

        # Check PK
        if pg_field.primary:
            options.append('pk')

        # Check not null
        if pg_field.mandatory:
            options.append('not null')

        return options

    def buildFieldOptionsStr(self, field_options):
        if len(field_options) == 0:
            return ""

        return ' [' + ' ,'.join(field_options) + ']'

    def convertFromPGTables(self, pg_tables):
        f = open(self.save_path + "/dbdiagramio.txt", "w+")

        for table in pg_tables:
            # Write open table def
            table_name_safe = self.makeStrSafe(table.name)
            f.write("Table " + table_name_safe + " {\n")

            for field in table.fields:
                # Build options array
                field_options = self.buildFieldOptions(field)

                # Check FK
                if field.fk_table_ind is not None and field.fk_field_ind is not None:
                    fk_table = pg_tables[field.fk_table_ind]
                    fk_field = fk_table.fields[field.fk_field_ind]

                    fk_table_name_safe = self.makeStrSafe(fk_table.name)
                    fk_field_name_safe = self.makeStrSafe(fk_field.name)

                    field_options.append('ref: > ' + fk_table_name_safe + '.' + fk_field_name_safe)

                # Build options string
                field_options_str = self.buildFieldOptionsStr(field_options)

                # Check type
                f_type = ' ' + field.f_type if field.f_type is not None else ' '
                if field.max_width is not None:
                    f_type = f_type + '(' + field.max_width + ')'

                # Write Field
                field_name_safe = self.makeStrSafe(field.name)
                f.write("   " + field_name_safe + f_type + field_options_str + "\n")
            # Write a new line and close table def
            f.write("}\r\n")

        print(self.save_path)
