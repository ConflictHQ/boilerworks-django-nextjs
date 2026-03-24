import json
import os
import pathlib
import urllib.parse
from textwrap import dedent

_backend_root = pathlib.Path(__file__).parent.resolve() / ".." / ".." / ".."
URLS = {
    'Dev': "https://app.dev.boilerworks.net/app/gql/config/#query=",
    'Local': "http://localhost:8000/app/gql/config/#query=",
}


def _classify_operation(gql_request):
    """Classify a GraphQL request as 'queries' or 'mutations'."""
    stripped = gql_request.strip()
    if stripped.startswith("mutation"):
        return "mutations"
    return "queries"


def _get_docs_path(function, gql_request):
    """Build the docs path based on the app name and operation type.

    Uses function.__module__ to determine the app (e.g. 'myapp.tests.test_mutations' -> 'myapp')
    and inspects gql_request to classify as query or mutation.
    """
    app_name = function.__module__.split('.')[0]
    operation_type = _classify_operation(gql_request)
    docs_dir = _backend_root / app_name / "docs" / "gql" / operation_type
    os.makedirs(docs_dir, exist_ok=True)
    return str(docs_dir) + "/"


def add_subtitle(file, subtitle):
    file.write("## " + subtitle + "\n")


def add_title(file, title):
    file.write("# " + title + "\n")


def add_codeblock(file, language, code):
    file.write("```" + language + "\n")
    file.write(code)
    file.write("\n```\n")


def add_paragraph(file, paragraph):
    if paragraph:
        file.write("\n" + dedent(paragraph) + "\n")


def url_gql_encode(url, query, variables):
    if not url:
        url = "/app/gql/config/#query="

    return url + urllib.parse.quote(query, safe='') + "&variables=" + urllib.parse.quote(variables, safe='')


def add_graphiql_url(file, query, variables):
    file.write("### See in GraphiQl!\n")
    for name, url in URLS.items():
        escaped_url = url_gql_encode(url, query, variables)
        file.write(f"- [{name}]({escaped_url})\n")
    file.write("\n<sup>*\\*You may need to update the url host and port*</sub>\n")


class DocWriter:

    @classmethod
    def write_to_doc(cls, function, variables, gql_request, response):
        caller_function_name = function.__name__
        variables = json.dumps(variables, indent=4)
        gql_request = dedent(gql_request)
        response = json.dumps(response, indent=4)
        docs_path = _get_docs_path(function, gql_request)
        with open(docs_path + caller_function_name.replace("test_", "") + ".md", "w") as file:
            add_title(file, caller_function_name.replace("test_", ""))
            add_graphiql_url(file, gql_request, variables)
            add_paragraph(file, function.__doc__)
            add_subtitle(file, "Variables")
            add_codeblock(file, "json", variables)
            add_subtitle(file, "Request")
            add_codeblock(file, "graphql", gql_request)
            add_subtitle(file, "Response")
            add_codeblock(file, "json", response)
