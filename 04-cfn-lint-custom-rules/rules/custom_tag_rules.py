"""
Custom cfn-lint rules: required tags based on resource properties.

  E9001  AWS::EC2::Instance  - InstanceType -> required tag
  E9002  AWS::EC2::Volume    - VolumeType gp3 -> Priority tag in a numeric range
  E9003  AWS::S3::Bucket     - PublicAccessBlockConfiguration with false -> tag

Every tag name, value and threshold is configurable through .cfnlintrc
(configure_rules) or on the command line (--configure-rule).
"""

from cfnlint.rules import CloudFormationLintRule, RuleMatch


def get_tags(properties):
    """Return the resource Tags as a {key: value} dict (values lowercased strings)."""
    tags = {}
    for tag in properties.get("Tags", []) or []:
        if isinstance(tag, dict) and "Key" in tag:
            value = tag.get("Value")
            # YAML turns unquoted true/false into booleans; normalise them
            if isinstance(value, bool):
                value = str(value).lower()
            tags[str(tag["Key"])] = value
    return tags


def resolve_value(cfn, value):
    """Return a literal value, following a Ref to a parameter's Default if needed."""
    if isinstance(value, dict) and list(value.keys()) == ["Ref"]:
        param = cfn.template.get("Parameters", {}).get(value["Ref"], {})
        return param.get("Default")
    return value


class InstanceTypeRequiredTags(CloudFormationLintRule):
    id = "E9001"
    shortdesc = "EC2 instance type requires a specific tag"
    description = (
        "Free-tier instance types (default t2.micro) must have the tag "
        "FreeTierEligible=true; performance instance types (default m5.large) "
        "must have the tag PerformanceCritical=true|false."
    )
    source_url = "https://github.com/aws-cloudformation/cfn-lint/blob/main/docs/getting_started/rules.md"
    tags = ["resources", "ec2", "tags", "custom"]

    def __init__(self):
        super().__init__()
        self.config_definition = {
            "free_tier_instance_types": {"default": ["t2.micro"], "type": "list", "itemtype": "string"},
            "free_tier_tag_key": {"default": "FreeTierEligible", "type": "string"},
            "free_tier_tag_values": {"default": ["true"], "type": "list", "itemtype": "string"},
            "performance_instance_types": {"default": ["m5.large"], "type": "list", "itemtype": "string"},
            "performance_tag_key": {"default": "PerformanceCritical", "type": "string"},
            "performance_tag_values": {"default": ["true", "false"], "type": "list", "itemtype": "string"},
        }
        self.configure()

    def _check(self, name, tags, instance_type, key, allowed):
        path = ["Resources", name, "Properties", "Tags"]
        if key not in tags:
            return [RuleMatch(path, f"Instance {name} ({instance_type}) must have tag '{key}' "
                                    f"with value {' or '.join(allowed)}")]
        if str(tags[key]).lower() not in [a.lower() for a in allowed]:
            return [RuleMatch(path, f"Instance {name} ({instance_type}) tag '{key}' is "
                                    f"'{tags[key]}', expected {' or '.join(allowed)}")]
        return []

    def match(self, cfn):
        matches = []
        for name, resource in cfn.get_resources(["AWS::EC2::Instance"]).items():
            props = resource.get("Properties", {}) or {}
            instance_type = resolve_value(cfn, props.get("InstanceType"))
            if not isinstance(instance_type, str):
                continue
            tags = get_tags(props)
            if instance_type in self.config["free_tier_instance_types"]:
                matches += self._check(name, tags, instance_type,
                                       self.config["free_tier_tag_key"],
                                       self.config["free_tier_tag_values"])
            if instance_type in self.config["performance_instance_types"]:
                matches += self._check(name, tags, instance_type,
                                       self.config["performance_tag_key"],
                                       self.config["performance_tag_values"])
        return matches


class Gp3VolumePriorityTag(CloudFormationLintRule):
    id = "E9002"
    shortdesc = "gp3 volumes require a Priority tag in range"
    description = (
        "AWS::EC2::Volume with VolumeType gp3 must have the tag Priority "
        "with a numeric value between 3000 and 16000 (inclusive)."
    )
    source_url = "https://github.com/aws-cloudformation/cfn-lint/blob/main/docs/getting_started/rules.md"
    tags = ["resources", "ec2", "ebs", "tags", "custom"]

    def __init__(self):
        super().__init__()
        self.config_definition = {
            "volume_types": {"default": ["gp3"], "type": "list", "itemtype": "string"},
            "priority_tag_key": {"default": "Priority", "type": "string"},
            "priority_min": {"default": 3000, "type": "integer"},
            "priority_max": {"default": 16000, "type": "integer"},
        }
        self.configure()

    def match(self, cfn):
        matches = []
        key = self.config["priority_tag_key"]
        low, high = self.config["priority_min"], self.config["priority_max"]
        for name, resource in cfn.get_resources(["AWS::EC2::Volume"]).items():
            props = resource.get("Properties", {}) or {}
            volume_type = resolve_value(cfn, props.get("VolumeType"))
            if volume_type not in self.config["volume_types"]:
                continue
            tags = get_tags(props)
            path = ["Resources", name, "Properties", "Tags"]
            if key not in tags:
                matches.append(RuleMatch(path, f"Volume {name} ({volume_type}) must have tag "
                                               f"'{key}' with a value between {low} and {high}"))
                continue
            try:
                priority = int(str(tags[key]))
            except ValueError:
                matches.append(RuleMatch(path, f"Volume {name} tag '{key}' must be a number, "
                                               f"got '{tags[key]}'"))
                continue
            if not low <= priority <= high:
                matches.append(RuleMatch(path, f"Volume {name} tag '{key}' is {priority}, "
                                               f"must be between {low} and {high}"))
        return matches


class PublicAccessAllowedTag(CloudFormationLintRule):
    id = "E9003"
    shortdesc = "S3 bucket with relaxed public access block requires a tag"
    description = (
        "If any PublicAccessBlockConfiguration setting of an AWS::S3::Bucket is "
        "false, the bucket must have the tag PublicAccessAllowed=true."
    )
    source_url = "https://github.com/aws-cloudformation/cfn-lint/blob/main/docs/getting_started/rules.md"
    tags = ["resources", "s3", "tags", "security", "custom"]

    def __init__(self):
        super().__init__()
        self.config_definition = {
            "checked_settings": {
                "default": ["BlockPublicAcls", "BlockPublicPolicy",
                            "IgnorePublicAcls", "RestrictPublicBuckets"],
                "type": "list", "itemtype": "string",
            },
            "public_access_tag_key": {"default": "PublicAccessAllowed", "type": "string"},
            "public_access_tag_values": {"default": ["true"], "type": "list", "itemtype": "string"},
        }
        self.configure()

    def match(self, cfn):
        matches = []
        key = self.config["public_access_tag_key"]
        allowed = [v.lower() for v in self.config["public_access_tag_values"]]
        for name, resource in cfn.get_resources(["AWS::S3::Bucket"]).items():
            props = resource.get("Properties", {}) or {}
            pab = props.get("PublicAccessBlockConfiguration")
            if not isinstance(pab, dict):
                continue
            disabled = [s for s in self.config["checked_settings"]
                        if str(resolve_value(cfn, pab.get(s, True))).lower() == "false"]
            if not disabled:
                continue
            tags = get_tags(props)
            path = ["Resources", name, "Properties", "Tags"]
            if str(tags.get(key, "")).lower() not in allowed:
                matches.append(RuleMatch(path, f"Bucket {name} has {', '.join(disabled)} set to false "
                                               f"and must have tag '{key}' with value "
                                               f"{' or '.join(self.config['public_access_tag_values'])}"))
        return matches
