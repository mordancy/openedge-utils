import re


class PG_Field:
    """
    A class used to represent a progress database field
    """
    def __init__(self, name, f_type=None, description="", f_format="", initial="", label="", position=None, max_width=None,
                 column_label="", f_help="", order=None, fk_table_ind=None, fk_field_ind=None, primary=None, mandatory=None):
        """
        Initializes the class
        :param name: (Required) initial table name
        """
        self.name = name
        self.f_type = f_type
        self.description = description
        self.f_format = f_format
        self.initial = initial
        self.label = label
        self.position = position
        self.max_width = max_width
        self.column_label = column_label
        self.f_help = f_help
        self.order = order
        self.fk_table_ind = fk_table_ind
        self.fk_field_ind = fk_field_ind
        self.primary = primary
        self.mandatory = mandatory

    def __repr__(self):
        """
        Creates the print representation of this class
        """
        return "Field {0} [PRIMARY={1}]".format(self.name, self.primary)

    def processTable(self, line_value):
        """
        Finds the table that this field pertains to
        """
        return re.search('"(.*)"', str.split(line_value, 'OF')[1]).group(1)

    def processType(self, line):
        """
        Finds the data type for the field
        """
        if 'AS' in line:
            self.f_type = str.strip(str.split(line, 'AS')[1])

    def processLine(self, line_type, line_value):
        """
        Processes a line and sets a field attribute to the determined value
        """
        if "attr-" in line_type:
            setattr(self, str.split(line_type, '-')[1], line_value)


class PG_Table:
    def __init__(self, name, area="", label="", description="", dump_name=""):
        self.name = name
        self.area = area
        self.label = label
        self.description = description
        self.dump_name = dump_name
        self.fields = []

    def __repr__(self):
        return "Table: " + self.name

    def processLine(self, line_type, line_value):
        if "attr-" in line_type:
            setattr(self, str.split(line_type, '-')[1], line_value)


class PG_Processor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tables = []

    def findTableByName(self, name: str):
        i = 0
        for table in self.tables:
            if table.name == name:
                return i
            # Iterate
            i += 1
        # Nothing found
        return None

    def findFieldByName(self, table_ind, field_name):
        i = 0
        if len(self.tables) > table_ind and table_ind >= 0:
            for field in self.tables[table_ind].fields:
                if field.name == field_name:
                    return i
                # Iterate
                i += 1
        else:
            # Not in bounds
            return None
        # Nothing found
        return None

    def fkCheck(self, field_name):
        """
        Attempts to find a foreign key by splitting the field name by - and looking for matching tables.
        :param field_name: str
        :return: tuple
        """
        if '-' in field_name:
            t_check = field_name.split('-')[0]
            t_match = self.findTableByName(t_check)
            if t_match is not None:
                f_match = self.findFieldByName(t_match, field_name)
                if f_match is not None:
                    # We matched and table and table field
                    return t_match, f_match
                else:
                    # Matching table but no matching field
                    return None, None
            else:
                # No matching table
                return None, None
        else:
            # Can not split field name
            return None, None

    def processFile(self):
        with open(self.file_path, 'r') as f_io:
            line = f_io.readline()
            i = 0

            current_mode = None
            current_table_ind = None
            current_field_ind = None

            while line:
                # Prep Line
                line = line.strip()

                # Get Line Information
                line_type = getLineType(line)
                line_value = getLineValue(line_type, line)

                if line_type == "NEW TABLE":
                    # Insert New Table and Store Index
                    current_mode = "TABLE DEFINITION"
                    self.tables.append(PG_Table(line_value))
                    current_table_ind = len(self.tables) - 1
                elif line_type == "NEW FIELD":
                    # Creates a New Field
                    current_mode = "FIELD DEFINITION"
                    current_field = PG_Field(line_value)

                    # Foreign Key Check - We should check before we insert
                    fk_table, fk_field = self.fkCheck(current_field.name)
                    if fk_field is not None and fk_field is not None:
                        # Assign the foreign key
                        current_field.fk_table_ind = fk_table
                        current_field.fk_field_ind = fk_field

                    # Find the field type
                    current_field.processType(line)

                    # Find table name of field
                    current_field_table_name = current_field.processTable(line)

                    # Find table pertaining to field
                    current_table_ind = self.findTableByName(current_field_table_name)
                    if current_table_ind is not None:
                        # Found the table, insert the field
                        self.tables[current_table_ind].fields.append(current_field)
                        current_field_ind = len(self.tables[current_table_ind].fields) - 1
                    else:
                        # Could not find the table, revert mode
                        current_mode = None
                elif line_type == "NEW INDEX":
                    current_mode = None
                else:
                    if line_type is not None:
                        if current_mode == "TABLE DEFINITION":
                            self.tables[current_table_ind].processLine(line_type, line_value)
                        elif current_mode == "FIELD DEFINITION":
                            self.tables[current_table_ind].fields[current_field_ind].processLine(line_type, line_value)

                # Read Next Line
                line = f_io.readline()
                i += 1
        return self.tables

    def filterByTable(self, table_name):
        if '"' in table_name:
            table_name = re.search('"(.*)"', table_name).group(1)

        t_match = self.findTableByName(table_name)
        if t_match is None:
            print("Filter table not found, skipping...")
            return self.tables

        # Create a temp table to store kept tables
        tables_filtered = [self.tables[t_match]]

        for field in self.tables[t_match].fields:
            # We found a foreign key
            if field.fk_table_ind is not None and field.fk_field_ind is not None:
                # We only do a first order filter, so blank any other foreign keys
                for field2 in self.tables[field.fk_table_ind].fields:
                    field2.fk_table_ind = None
                    field2.fk_field_ind = None
                # Add to our temp table
                tables_filtered.append(self.tables[field.fk_table_ind])
                # Rebuild foreign key index
                field.fk_table_ind = len(tables_filtered) - 1

        # Store the tables we found
        self.tables = tables_filtered

        print("Filtered to " + str(len(tables_filtered)) + " tables.")
        return self.tables


def getLineType(line):
    if 'ADD TABLE "' in line:
        return "NEW TABLE"
    elif 'ADD FIELD' in line:
        return "NEW FIELD"
    elif 'ADD INDEX "' in line:
        return "NEW INDEX"
    elif 'AREA "' in line:
        return "attr-area"
    elif 'LABEL "' in line:
        return "attr-label"
    elif 'DESCRIPTION "' in line:
        return "attr-description"
    elif 'DUMP-NAME "' in line:
        return "attr-dump_name"
    elif 'FORMAT "' in line:
        return "attr-f_format"
    elif 'PRIMARY' in line:
        return "attr-primary"
    elif 'MANDATORY' in line:
        return "attr-mandatory"
    elif 'MAX-WIDTH' in line:
        return "attr-max_width"
    else:
        return None


def getLineValue(line_type, line):
    if line_type == "NEW TABLE" or line_type == "attr-name" or line_type == "attr-label" \
            or line_type == "attr-description" or line_type == "attr-dump_name" or line_type == "attr-f_format":
        if line.count('"') > 2:
            return re.search('"(.*)"', line).group(1)
        else:
            return str.split(line, '"')[1]
    elif line_type == "NEW FIELD":
        return re.search('"(.*)"', str.split(line, 'OF')[0]).group(1)
    elif line_type == "attr-max_width":
        return str.split(line, ' ')[1]
    elif line_type == "attr-primary" or line_type == "attr-mandatory":
        return True
    else:
        return None
