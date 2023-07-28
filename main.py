import csv
import os

import inquirer as inq
from validate_email import validate_email


class ContactValidationException(Exception):
    def __init__(self, cause, solution=None):
        self.message = cause
        self.solution = solution

    def __str__(self):
        return self.message + "; " + self.solution

    @staticmethod
    def not_str_x(x):
        return ContactValidationException(x + " value is not a string", "make sure " + x + " value is a string")

    @staticmethod
    def not_str_name():
        return ContactValidationException.not_str_x("name")

    @staticmethod
    def not_str_phone():
        return ContactValidationException.not_str_x("phone")

    @staticmethod
    def not_str_email():
        return ContactValidationException.not_str_x("email")

    @staticmethod
    def empty_x(x):
        return ContactValidationException(x + " is empty", "please provide a non-empty " + x)

    @staticmethod
    def empty_name():
        return ContactValidationException.empty_x("name")

    @staticmethod
    def empty_phone():
        return ContactValidationException.empty_x("phone")

    @staticmethod
    def malformed_email():
        return ContactValidationException("email is malformed", "please provide a valid email")


class Contact:
    def __init__(self, name, phone, email):
        # All properties should be of type string.
        if not isinstance(name, str):
            raise ContactValidationException.not_str_name()
        if not isinstance(phone, str):
            raise ContactValidationException.not_str_phone()
        if not isinstance(email, str) and email is not None:
            raise ContactValidationException.not_str_email()

        # Name and phone should not be empty; email however, is optional, and can be empty/None.
        if len(name) == 0:
            raise ContactValidationException.empty_name()
        if len(phone) == 0:
            raise ContactValidationException.empty_phone()

        # Email should be valid.
        if email is not None and len(email) > 0 and not validate_email(email):
            raise ContactValidationException.malformed_email()

        # Name can be any string; phone also (there are recommendations around how a phone should be, but no enforcement).
        self.name = name
        self.phone = phone
        self.email = email

    # name / phone / email
    def __str__(self):
        return '🧑 {} / ☎ {}'.format(self.name, self.phone) + \
               (' / 📧 {}'.format(self.email) if (self.email is not None and len(self.email) > 0) else "")


# Store all contacts in a dictionary; each associated with an integer id key.
contacts = {}
next_id = 0


# List (print out) contacts of given ids (identifiers).
# Named "listt" to avoid conflict with the built-in function "list".
def listt(ids):
    # Named "idd" to avoid conflict with built-in function "id".
    for idd in ids:
        contact = contacts[idd]
        print(contact)


# Query contacts by a string (in name, phone, and email); returns a list of ids.
def query(q):
    q = q.lower()  # Case-insensitive query.
    ids = []
    # Named "idd" to avoid conflict with built-in function "id".
    for idd in contacts:
        contact = contacts[idd]

        # Compare properties in lower-case; cause query is case-insensitive.
        if q in contact.name.lower():
            ids.append(idd)
        elif q in contact.phone.lower():
            ids.append(idd)
        elif contact.email is not None and q in contact.email.lower():
            ids.append(idd)

    return ids


# Prompt to create a new contact.
def action_create():
    global next_id
    anss = inq.prompt([
        inq.Text("name", "Name"),
        inq.Text("phone", "phone"),
        inq.Text("email", "Email")
    ], raise_keyboard_interrupt=True)

    print()

    try:
        contacts[next_id] = Contact(anss["name"], anss["phone"], anss["email"])
        next_id += 1
        print("✔ Created!")
    except ContactValidationException as e:
        print("❌ Error:", str(e) + " 🤔.")

    print()


# Print out all contacts.
def action_list():
    if len(contacts) == 0:
        print("Empty 🤷! Try creating a new contact.")
    else:
        listt(contacts.keys())
    print()


# Prompt to search in contacts (in name, phone, and email).
def action_search():
    # Prompt to get a query string from the user.
    q = inq.prompt([inq.Text("q", "Query")], raise_keyboard_interrupt=True)["q"]
    print()
    if q is not None and len(q) > 0:
        ids = query(q)
        if len(ids) > 0:
            listt(ids)
        else:
            print("Found no matches 🤦! Try a different query.")
    else:
        print("Empty query 🤷! Please provide a non-empty query text.")
    print()


# Prompt to delete a contact.
# First, asks for a query and searches contacts; if multiple contacts matched, user have to choose one.
def action_delete():
    # Prompt to get a query string from the user.
    q = inq.prompt([inq.Text("q", "Query")], raise_keyboard_interrupt=True)["q"]
    print()
    if q is not None and len(q) > 0:
        ids = query(q)
        to_delete_id = None
        if len(ids) == 1:  # The query matched with one id; perfect!
            to_delete_id = ids[0]
            print(contacts[to_delete_id])  # Print out the contact before deletion.
            print()
        elif len(ids) > 0:  # The query matched with more than one id; let the user choose one.
            # Prompt to let the user choose.
            choices = list(map(lambda idd: (str(contacts[idd]), idd), ids))
            to_delete_id = inq.prompt([inq.List("id", "Select one to delete", choices)], raise_keyboard_interrupt=True)[
                "id"]

        if to_delete_id is not None:
            # Confirm deletion
            y = inq.prompt([inq.Confirm("y", message="Are you sure", default=None)], raise_keyboard_interrupt=True)["y"]

            if y is None:  # To work around a bug.
                print()
                y = False

            if y:
                del contacts[to_delete_id]
                print("✔ Deleted!")
            else:
                print("❌ Deletion cancelled.")
        else:
            print("Found no matches 🤦! Try a different query.")
    else:
        print("Empty query 🤷! Please provide a non-empty query text.")
    print()


# Import/Export file path.
path = os.path.join(os.getcwd(), "contacts.csv")  # Equal to "./contacts.csv" in GNU/Linux.


# Export contacts to a csv file.
def action_export():
    with open(path, "wt", newline="") as csv_file:
        w = csv.DictWriter(f=csv_file, fieldnames=["name", "phone", "email"])
        w.writeheader()
        w.writerows(map(lambda idd: vars(contacts[idd]), contacts.keys()))
    if len(contacts) == 0:
        print("✔ Exported (although empty 🤷)!")
    else:
        print("✔ Exported!")
    print()


# Import contacts from a csv file; it adds them to the current set of contacts.
def action_import():
    global next_id

    try:
        any_row_error = False  # Did we hit any error (errors are per row, and erroneous rows are logged and skipped)?
        count = 0  # Count of imported contacts.

        with open(path, "rt", newline="") as f:
            r = csv.DictReader(f)

            for row_i, row in enumerate(r):
                name = row.get("name")
                phone = row.get("phone")
                email = row.get("email")

                try:
                    # Some external validation to ensure good error messages.
                    if name is None:
                        raise ContactValidationException.empty_name()
                    if phone is None:
                        raise ContactValidationException.empty_phone()

                    contacts[next_id] = Contact(name, phone, email)
                    next_id += 1
                    count += 1
                except ContactValidationException as e:
                    print("❌ Error in row {} (skipping):".format(row_i), str(e) + " 🤔.")
                    any_row_error = True

        if any_row_error:
            print()  # If any error got logged, print an empty line to balance the output.

        if count > 0:
            print("✔ Imported {}!".format(count))
        elif count == 0:
            print("✔ Imported nothing 🤷!")
        print()
    except FileNotFoundError as e:
        print(
            "❌ {} file not found!\n📄 Put your CSV file in the current working directory as contacts.csv to be able to import it.".format(
                e.filename))
        print()


# Action name: Action function
actions = {
    "📖 List": action_list,
    "🔍 Search": action_search,
    "🧑 Create": action_create,
    "🧹 Delete": action_delete,
    "🚢 Export CSV": action_export,
    "📥 Import CSV": action_import,
    "❌ Exit": None  # Exit action function is handled in the main menu loop (breaks the loop).
}

# Keep track of last action to highlight it after an operation finished.
last_action = list(actions.keys())[0]
# Main menu loop.
while True:
    # Prompt to let the user choose what to do.
    try:
        action = inq.prompt(
            questions=[inq.List(name="act", message="Main menu", choices=actions.keys(), default=last_action)],
            raise_keyboard_interrupt=True
        )["act"]
        if action == "❌ Exit":
            print("👋 Bye")
            break
        else:
            try:
                actions[action]()
            except KeyboardInterrupt:
                print()
                print("Interrupted the current action 🤷.")
                print()
        last_action = action
    except KeyboardInterrupt:
        print("👋 Bye")
        break
