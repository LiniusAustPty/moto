import json
from urllib.parse import urlparse

from moto.core.responses import BaseResponse
from moto.core.utils import amzn_request_id
from .models import databrew_backends


class DataBrewResponse(BaseResponse):
    SERVICE_NAME = "databrew"

    @property
    def databrew_backend(self):
        """Return backend instance specific for this region."""
        return databrew_backends[self.region]

    @property
    def parameters(self):
        return json.loads(self.body)

    @amzn_request_id
    def create_recipe(self):
        # https://docs.aws.amazon.com/databrew/latest/dg/API_CreateRecipe.html
        recipe_description = self.parameters.get("Description")
        recipe_steps = self.parameters.get("Steps")
        recipe_name = self.parameters.get("Name")
        tags = self.parameters.get("Tags")
        return json.dumps(
            self.databrew_backend.create_recipe(
                recipe_name, recipe_description, recipe_steps, tags
            ).as_dict()
        )

    @amzn_request_id
    def delete_recipe_version(self, request, full_url, headers):
        self.setup_class(request, full_url, headers)
        # https://docs.aws.amazon.com/databrew/latest/dg/API_DeleteRecipeVersion.html
        if request.method == "DELETE":
            parsed_url = urlparse(full_url)
            split_path = parsed_url.path.strip("/").split("/")
            recipe_name = split_path[1]
            recipe_version = split_path[3]
            self.databrew_backend.delete_recipe_version(recipe_name, recipe_version)
            return (
                200,
                {},
                json.dumps({"Name": recipe_name, "RecipeVersion": recipe_version}),
            )

    @amzn_request_id
    def list_recipes(self):
        # https://docs.aws.amazon.com/databrew/latest/dg/API_ListRecipes.html
        next_token = self._get_param("NextToken", self._get_param("nextToken"))
        max_results = self._get_int_param(
            "MaxResults", self._get_int_param("maxResults")
        )
        recipe_version = self._get_param(
            "RecipeVersion", self._get_param("recipeVersion")
        )

        # pylint: disable=unexpected-keyword-arg, unbalanced-tuple-unpacking
        recipe_list, next_token = self.databrew_backend.list_recipes(
            next_token=next_token,
            max_results=max_results,
            recipe_version=recipe_version,
        )
        return json.dumps(
            {
                "Recipes": [recipe.as_dict() for recipe in recipe_list],
                "NextToken": next_token,
            }
        )

    @amzn_request_id
    def list_recipe_versions(self, request, full_url, headers):
        # https://docs.aws.amazon.com/databrew/latest/dg/API_ListRecipeVersions.html
        self.setup_class(request, full_url, headers)
        recipe_name = self._get_param("Name", self._get_param("name"))
        next_token = self._get_param("NextToken", self._get_param("nextToken"))
        max_results = self._get_int_param(
            "MaxResults", self._get_int_param("maxResults")
        )

        # pylint: disable=unexpected-keyword-arg, unbalanced-tuple-unpacking
        recipe_list, next_token = self.databrew_backend.list_recipe_versions(
            recipe_name=recipe_name, next_token=next_token, max_results=max_results
        )
        return json.dumps(
            {
                "Recipes": [recipe.as_dict() for recipe in recipe_list],
                "NextToken": next_token,
            }
        )

    @amzn_request_id
    def publish_recipe(self, request, full_url, headers):
        self.setup_class(request, full_url, headers)
        if request.method == "POST":
            parsed_url = urlparse(full_url)
            recipe_name = parsed_url.path.strip("/").split("/", 2)[1]
            recipe_description = self.parameters.get("Description")
            self.databrew_backend.publish_recipe(recipe_name, recipe_description)
            return 200, {}, json.dumps({"Name": recipe_name})

    def put_recipe_response(self, recipe_name):
        recipe_description = self.parameters.get("Description")
        recipe_steps = self.parameters.get("Steps")

        self.databrew_backend.update_recipe(
            recipe_name, recipe_description, recipe_steps
        )
        return 200, {}, json.dumps({"Name": recipe_name})

    def get_recipe_response(self, recipe_name):
        # https://docs.aws.amazon.com/databrew/latest/dg/API_DescribeRecipe.html
        recipe_version = self._get_param(
            "RecipeVersion", self._get_param("recipeVersion")
        )
        recipe = self.databrew_backend.get_recipe(
            recipe_name, recipe_version=recipe_version
        )
        return 200, {}, json.dumps(recipe.as_dict())

    @amzn_request_id
    def recipe_response(self, request, full_url, headers):
        self.setup_class(request, full_url, headers)
        parsed_url = urlparse(full_url)

        recipe_name = parsed_url.path.rstrip("/").rsplit("/", 1)[1]

        if request.method == "PUT":
            return self.put_recipe_response(recipe_name)
        elif request.method == "GET":
            return self.get_recipe_response(recipe_name)

    @amzn_request_id
    def create_ruleset(self):
        ruleset_description = self.parameters.get("Description")
        ruleset_rules = self.parameters.get("Rules")
        ruleset_name = self.parameters.get("Name")
        ruleset_target_arn = self.parameters.get("TargetArn")
        tags = self.parameters.get("Tags")

        return json.dumps(
            self.databrew_backend.create_ruleset(
                ruleset_name,
                ruleset_description,
                ruleset_rules,
                ruleset_target_arn,
                tags,
            ).as_dict()
        )

    def put_ruleset_response(self, ruleset_name):
        ruleset_description = self.parameters.get("Description")
        ruleset_rules = self.parameters.get("Rules")
        tags = self.parameters.get("Tags")

        ruleset = self.databrew_backend.update_ruleset(
            ruleset_name, ruleset_description, ruleset_rules, tags
        )
        return 200, {}, json.dumps(ruleset.as_dict())

    def get_ruleset_response(self, ruleset_name):
        ruleset = self.databrew_backend.get_ruleset(ruleset_name)
        return 201, {}, json.dumps(ruleset.as_dict())

    def delete_ruleset_response(self, ruleset_name):
        self.databrew_backend.delete_ruleset(ruleset_name)
        return 204, {}, ""

    @amzn_request_id
    def ruleset_response(self, request, full_url, headers):
        self.setup_class(request, full_url, headers)
        parsed_url = urlparse(full_url)

        ruleset_name = parsed_url.path.split("/")[-1]

        if request.method == "PUT":
            response = self.put_ruleset_response(ruleset_name)
            return response
        elif request.method == "GET":
            return self.get_ruleset_response(ruleset_name)
        elif request.method == "DELETE":
            return self.delete_ruleset_response(ruleset_name)

    @amzn_request_id
    def list_rulesets(self):
        # https://docs.aws.amazon.com/databrew/latest/dg/API_ListRulesets.html
        next_token = self._get_param("NextToken", self._get_param("nextToken"))
        max_results = self._get_int_param(
            "MaxResults", self._get_int_param("maxResults")
        )

        # pylint: disable=unexpected-keyword-arg, unbalanced-tuple-unpacking
        ruleset_list, next_token = self.databrew_backend.list_rulesets(
            next_token=next_token, max_results=max_results
        )
        return json.dumps(
            {
                "Rulesets": [ruleset.as_dict() for ruleset in ruleset_list],
                "NextToken": next_token,
            }
        )
