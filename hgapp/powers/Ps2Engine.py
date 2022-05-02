import json, logging
from collections import defaultdict, Counter
from django.urls import reverse

from django.db.models import Prefetch
from .models import PowerSystem, EPHEMERAL, UNIQUE, ADDITIVE, SUB_JOINING_AND, SUB_JOINING_OR, SUB_ALL, \
    ADDITIVE

from characters.models import STATUS_SEASONED, STATUS_VETERAN, STATUS_ANY


def merge_status(current_status, incoming_status):
    if not current_status:
        return incoming_status
    if incoming_status == STATUS_SEASONED and current_status != STATUS_VETERAN:
        return STATUS_SEASONED
    if incoming_status == STATUS_VETERAN:
        return STATUS_VETERAN

class PowerEngine:

    def __init__(self):
        self.blob = PowerSystem.get_singleton().get_python()

    def get_json_power_blob(self):
        return json.dumps(self.blob)

    def calculate_req_status(self, effect_id, vector_id, modality_id, modifier_instances, param_instances):
        # TODO: Enhancement group status requirements
        current_status = None
        components = self.components_from_model(effect_id, vector_id, modality_id)
        """
        
        let active_groups = this.enhancements.filter(enh => null != enh.group)
            .map(enh => powerBlob["enhancement_group_by_pk"][enh.group]).filter(onlyUnique);
        """
        active_groups = Counter()
        for component in components:
            current_status = merge_status(current_status, component["required_status"][0])
        for mod_inst in modifier_instances:
            mod, mod_type = self.get_mod_and_type_for_inst(mod_inst)
            if mod_type == "enh^" and mod["group"]:
                active_groups[mod["group"]] += 1
            current_status = merge_status(current_status, mod["required_status"][0])
        for param_inst in param_instances:
            pow_param = param_inst.relevant_power_param
            if param_inst.value >= pow_param.veteran:
                current_status = merge_status(current_status, STATUS_VETERAN)
            elif param_inst.value >= pow_param.seasoned:
                current_status = merge_status(current_status, STATUS_SEASONED)
        for group in active_groups:
            count = active_groups[group]
            if count >= self.blob[PowerSystem.ENHANCEMENT_GROUP_BY_PK][group]["seasoned_threshold"]:
                current_status = merge_status(current_status, STATUS_SEASONED)
            if count >= self.blob[PowerSystem.ENHANCEMENT_GROUP_BY_PK][group]["veteran_threshold"]:
                current_status = merge_status(current_status, STATUS_VETERAN)
        return current_status if current_status else STATUS_ANY


    def validate_components(self, effect_id, vector_id, modality_id):
        effect = self.blob[PowerSystem.EFFECTS][effect_id]
        vector = self.blob[PowerSystem.VECTORS][vector_id]
        modality = self.blob[PowerSystem.MODALITIES][modality_id]
        # An Effect is only available on a given modality if it appears in this mapping.
        if not effect["slug"] in self.blob[PowerSystem.EFFECTS_BY_MODALITY][modality["slug"]]:
            raise ValueError("INVALID GIFT. Modality {} and Effect {} are incompatible".format(modality, effect))

        # A Vector is only available on a given Modality + Effect if it appears in both mappings.
        if not vector["slug"] in self.blob[PowerSystem.VECTORS_BY_EFFECT][effect["slug"]]:
            raise ValueError("INVALID GIFT. Vector {} and Effect {} are incompatible".format(vector, effect))
        if not vector["slug"] in self.blob[PowerSystem.VECTORS_BY_MODALITY][modality["slug"]]:
            raise ValueError("INVALID GIFT. Vector {} and Modality {} are incompatible".format(vector, modality))

    def validate_new_mod_forms(self, effect_id, vector_id, modality_id, modifier_forms):
        # Currently validates details text, modifier multiplicity count, and blacklist/component availability
        # TODO: validate required enhancements and drawbacks
        # TODO: validate mutual exclusivity (or maybe do this in system text rendering?)
        # TODO: validate min num required enhancements and drawbacks
        components = self.components_from_model(effect_id, vector_id, modality_id)
        allowed_enhancement_slugs = PowerEngine._get_allowed_modifiers_for_components(components, PowerSystem.ENHANCEMENTS)
        allowed_drawback_slugs = PowerEngine._get_allowed_modifiers_for_components(components, PowerSystem.DRAWBACKS)
        enhancements = self.blob[PowerSystem.ENHANCEMENTS]
        drawbacks = self.blob[PowerSystem.DRAWBACKS]
        new_enhancement_count_by_slug = {}
        new_drawback_count_by_slug = {}

        for form in modifier_forms:
            mod_slug = form.cleaned_data["mod_slug"]
            if form.cleaned_data["is_enhancement"]:
                modifier = enhancements[mod_slug]
                if mod_slug not in allowed_enhancement_slugs:
                    raise ValueError("Enhancement not allowed: {}. Allowed enhancement slugs:".format(
                        form.cleaned_data,
                        allowed_enhancement_slugs))
                count = new_enhancement_count_by_slug[mod_slug] if mod_slug in new_enhancement_count_by_slug else 0
                new_enhancement_count_by_slug[mod_slug] = count
            else:
                modifier = drawbacks[mod_slug]
                if mod_slug not in allowed_drawback_slugs:
                    raise ValueError("Drawback not allowed: {}. Allowed drawback slugs:".format(
                        form.cleaned_data,
                        allowed_drawback_slugs))
                count = new_drawback_count_by_slug[mod_slug] if mod_slug in new_drawback_count_by_slug else 0
                new_drawback_count_by_slug[mod_slug] = count

            # modifier details validation
            if modifier["detail_field_label"] and "details" not in form.cleaned_data:
                raise ValueError("Modifier must have details text submitted. Mod: {}, Form data: {}".format(
                    modifier,
                    form.cleaned_data))

            # modififier multiplicity validation
            if count > 1 and not modifier["multiplicity_allowed"]:
                raise ValueError("Multiple modifiers but multiplicity not allowed. Mod: {}, Form data: {}".format(
                    modifier,
                    form.cleaned_data))
            if count > 4:
                raise ValueError("More than 4 modifiers with multiplicity found. Mod: {}, Form data: {}".format(
                    modifier,
                    form.cleaned_data))

    def validate_new_param_forms(self, model_effect_id, model_vector_id, model_modality_id, param_formset):
        components = self.components_from_model(model_effect_id, model_vector_id, model_modality_id)
        allowed_power_params = PowerEngine._get_allowed_params_for_components(components)
        allowed_power_param_by_slug = {x["id"]: x for x in allowed_power_params}
        for form in param_formset:
            form_param_id = form.cleaned_data["power_param_id"]
            if form_param_id not in allowed_power_param_by_slug:
                raise ValueError("Power Param not available for components. components: {}, Form data: {}, allowed: {}".format(
                    components,
                    form.cleaned_data,
                    allowed_power_param_by_slug))
            power_param = allowed_power_param_by_slug[form_param_id]
            allowed_power_param_by_slug.pop(form_param_id)
            if not form.cleaned_data["level"]:
                # disabled param
                continue
            form_level = form.cleaned_data["level"]
            if form_level < 0 or form_level >= len(power_param["levels"]):
                raise ValueError("Invalid level for power param: {} level {}".format(
                    power_param,
                    form_level))

        if len(allowed_power_param_by_slug) > 0:
            raise ValueError("parameter not submitted in form: {}".format(allowed_power_param_by_slug))

    def validate_new_field_forms(self, model_effect_id, model_vector_id, model_modality_id, text_forms, weap_forms, roll_forms):
        components = self.components_from_model(model_effect_id, model_vector_id, model_modality_id)
        text_field_ids = set()
        weapon_field_ids = set()
        roll_field_ids = set()
        for component in components:
            if "text_fields" in component:
                text_field_ids.update(set([x["id"] for x in component["text_fields"]]))
            if "weapon_fields" in component:
                weapon_field_ids.update(set([x["id"] for x in component["weapon_fields"]]))
            if "roll_fields" in component:
                roll_field_ids.update(set([x["id"] for x in component["roll_fields"]]))
        for form in text_forms:
            field_id = form.cleaned_data["field_id"]
            if field_id not in text_field_ids:
                raise ValueError("field not expected: {}".format(form.cleaned_data))
        for form in weap_forms:
            field_id = form.cleaned_data["field_id"]
            if field_id not in weapon_field_ids:
                raise ValueError("field not expected: {}".format(form.cleaned_data))
        for form in roll_forms:
            field_id = form.cleaned_data["field_id"]
            if field_id not in roll_field_ids:
                raise ValueError("field not expected: {}".format(form.cleaned_data))

    def should_display_vector(self, effect_id, modality_id):
        effect = self.blob[PowerSystem.EFFECTS][effect_id]
        modality = self.blob[PowerSystem.MODALITIES][modality_id]
        avail_vec = set(self.blob[PowerSystem.VECTORS_BY_EFFECT][effect["slug"]])
        avail_vec = avail_vec.intersection(set(self.blob[PowerSystem.VECTORS_BY_MODALITY][modality["slug"]]))
        return len(avail_vec) > 1

    def get_mod_and_type_for_inst(self, modifier_inst):
        if hasattr(modifier_inst, "relevant_enhancement"):
            modifier = self.blob[PowerSystem.ENHANCEMENTS][modifier_inst.relevant_enhancement_id]
            mod_type = "enh^"
        elif hasattr(modifier_inst, "relevant_drawback"):
            modifier = self.blob[PowerSystem.DRAWBACKS][modifier_inst.relevant_drawback_id]
            mod_type = "drawb^"
        else:
            raise ValueError("Unexpected modifier type" + modifier_inst)
        return modifier, mod_type

    @staticmethod
    def _get_allowed_params_for_components(components):
        params = []
        blacklist = []
        for component in components:
            params.extend(component["parameters"])
            blacklist.extend(component["blacklist_parameters"])
        print(params)
        print(blacklist)
        return [x for x in params if x["param_id"] not in blacklist]

    @staticmethod
    def _get_allowed_modifiers_for_components(components, modifier_type):
        blacklisted_mod_slugs = set()
        selected_mod_slugs = set()
        for component in components:
            blacklisted_mod_slugs.update(set([mod_slug for mod_slug in component["blacklist_" + modifier_type]]))
            selected_mod_slugs.update(set([mod_slug for mod_slug in component[modifier_type]]))
        allowed_modifiers = selected_mod_slugs.difference(blacklisted_mod_slugs)
        return allowed_modifiers

    def components_from_model(self, effect_id, vector_id, modality_id):
        effect = self.blob[PowerSystem.EFFECTS][effect_id]
        vector = self.blob[PowerSystem.VECTORS][vector_id]
        modality = self.blob[PowerSystem.MODALITIES][modality_id]
        components = [effect, vector, modality]
        return components


class Substitution:
    def __init__(self, mode, replacement):
        self.mode = mode
        self.replacement = replacement

    def __repr__(self):
        return "mode: {}, replacement: {}".format(self.mode, self.replacement)


class ReplacementCandidate:
    def __init__(self, replacement_type, should_capitalize, markers, default_value, start, end):
        self.replacement_type = replacement_type
        self.should_capitalize = should_capitalize
        self.markers = markers
        self.default_value = default_value
        self.start = start
        self.end = end

    def __repr__(self):
        return "replacement_type: {}, markers: {}, start-end: {}-{}".format(self.replacement_type,
                                                                            self.markers,
                                                                            self.start,
                                                                            self.end)


# The code in this class MUST STAY IN SYNC with the FE code in ps2_create_script.js.
class SystemTextRenderer:
    paren_end_by_start = {
        '(': ')',
        '@': '%',
        '[': ']',
        '{': '}',
        '#': '+',
        ';': '/',
    }
    paren_join_string = {
        '(': ', ',
        '@': ', ',
        '[': ' ',
        '{': '</p><p>',
        '+': '',
        ';': "</li><li>",
    }

    def __init__(self, engine):
        self.system = engine

    def populate_rendered_fields(self, power, modifier_instances, param_instances, field_instances):
        vector = self.system.blob[PowerSystem.VECTORS][power.vector_id]
        effect = self.system.blob[PowerSystem.EFFECTS][power.base_id]
        modality = self.system.blob[PowerSystem.MODALITIES][power.modality_id]
        unrendered_system = "<p>" + vector["system_text"] + "</p><p>" + effect["system_text"] + "</p>"
        unrendered_description = modality["system_text"]
        replacement_map = self._build_replacement_map(power, modifier_instances, param_instances, field_instances)
        power.system = SystemTextRenderer._perform_system_text_replacements(unrendered_system, replacement_map)
        power.gift_summary = SystemTextRenderer._perform_system_text_replacements(unrendered_description, replacement_map)
        power.errata = SystemTextRenderer._perform_system_text_replacements("{{gift-errata}}", replacement_map)

    @staticmethod
    def _perform_system_text_replacements(unrendered_system, replacement_map):
        system_text = unrendered_system
        to_replace = SystemTextRenderer._find_replacement_candidate(system_text)
        replacement_count = 0
        while to_replace:
            system_text = SystemTextRenderer._replace_in_system_text(system_text, replacement_map, to_replace)
            to_replace = SystemTextRenderer._find_replacement_candidate(system_text)
            replacement_count += 1
            if replacement_count > 1000:
                raise ValueError("Over 1000 replacements. . . infinite loop?")
        return system_text


    @staticmethod
    def _find_replacement_candidate(system_text):
        marker_starts = ['(', '[', '{', '@', '#', ';']
        end_marker = None
        paren_depth = 0
        start = None
        end = None
        default_content_start_index = None
        capitalize = False

        # this little construction emulates a traditional for loop
        i = 0
        while i < len(system_text):
            cur_char = system_text[i]
            if i > 0 and system_text[i-1] == cur_char:
                if cur_char in marker_starts:
                    # two start markers
                    if start is None:
                        start = i - 1
                        marker_starts = [cur_char]
                        end_marker = SystemTextRenderer.paren_end_by_start[cur_char]
                    paren_depth = paren_depth + 1
                    # this avoids the case where we have four+ starts in a row ala [[[[
                    i += 1
                elif end_marker and cur_char == end_marker:
                    # two end markers
                    paren_depth -= 1
                    if paren_depth == 0:
                        end = i
                        if i+1 < len(system_text):
                            # if check for capitalization flag that appears immediately afterwards.
                            if system_text[i+1] == "^":
                                capitalize = True
                                end = i+1 # to also replace ^
                        break
                    else:
                        # this avoids the case where we have four+ ends in a row ala ]]]]
                        i += 1
            if start is not None and not default_content_start_index and cur_char == '|' and paren_depth == 1:
                default_content_start_index = i
            i += 1

        if start is None:
            # no candidate found
            return None

        if not end:
            raise ValueError("Unmatched start symbols found in system text: " + system_text)

        # Capitalization increases end by 1
        end_paren_index = end - 2 if capitalize else end - 1
        marker_end = end_paren_index if not default_content_start_index else default_content_start_index
        marker_section = system_text[start+2 : marker_end]
        marker_section = marker_section.strip()
        markers = marker_section.split(',')
        if marker_starts[0] not in ['(', '@', '#'] and len(markers) > 1:
            raise ValueError("too many marker strings for non-list sub starting at: " + start + "for text " + system_text)
        default_value = None
        if default_content_start_index:
            default_value = system_text[default_content_start_index + 1 : end - 1]
            default_value = default_value.strip()
        return ReplacementCandidate(marker_starts[0], capitalize, markers, default_value, start, end)


    # This method must remain functionally equal to ps2_create_script.js # buildReplacementMap
    # This is to ensure consistent server-side rendering of user-created powers.
    def _build_replacement_map(self, power, modifier_instances, param_instances, field_instances):
        # A map of marker string to list of replacements
        replacements = defaultdict(list)
        replacements["gift-name"].append(Substitution(UNIQUE, power.name))
        replacements = self._add_replacements_for_modifiers(replacements, modifier_instances)
        replacements = self._add_replacements_for_components(replacements, power)
        replacements = self._add_replacements_for_parameters(replacements, param_instances)
        replacements = self._add_replacements_for_fields(replacements, power, field_instances)
        replacements = self._collapse_substitutionss(replacements)
        return replacements

    # This method must remain functionally equal to ps2_create_script.js # addReplacementsForModifiers
    # This is to ensure consistent server-side rendering of user-created powers.
    # DO NOT REFACTOR THIS METHOD WITHOUT CHANGING THE ASSOCIATED METHOD IN THE FE
    def _add_replacements_for_modifiers(self, modifier_replacements, modifier_instances):
        # Key is triple of mod type, slug, and marker
        num_included_for_mod_marker = Counter()
        # This replicates the detailsByModifiers map in the FE
        details_by_mod = defaultdict(list)
        for modifier_inst in modifier_instances:
            modifier, mod_type = self.system.get_mod_and_type_for_inst(modifier_inst)
            details_by_mod[mod_type + modifier["slug"]].append(modifier_inst.detail)

        for modifier_inst in modifier_instances:
            modifier, mod_type = self.system.get_mod_and_type_for_inst(modifier_inst)
            mod_joining_strategy = modifier["joining_strategy"]
            mod_detail = modifier_inst.detail
            for sub in modifier["substitutions"]:
                marker = sub["marker"]
                replacement = sub["replacement"]
                count_for_marker = num_included_for_mod_marker[mod_type + modifier["slug"] + marker]
                if '$' in replacement:
                    if mod_joining_strategy != SUB_ALL:
                        all_details = details_by_mod[mod_type + modifier["slug"]]
                        all_details = [x for x in all_details if len(x) != 0]
                        joining_string = ", " if len(all_details) > 2 else " "
                        if len(all_details) > 1:
                            joining_word = "or " if mod_joining_strategy == SUB_JOINING_OR else "and "
                            all_details[-1] = joining_word + all_details[-1]
                        dollar_sub = joining_string.join(all_details)
                    else:
                        dollar_sub = mod_detail
                    replacement = SystemTextRenderer._sub_user_input_for_dollar(replacement, dollar_sub)
                new_sub = Substitution(sub["mode"], replacement)
                num_included_for_mod_marker[mod_type + modifier["slug"] + marker] += 1
                if mod_joining_strategy == SUB_ALL or count_for_marker == 0:
                    if sub["mode"] == UNIQUE and count_for_marker == 1:
                        continue
                    modifier_replacements[marker].append(new_sub)
        return modifier_replacements


    @staticmethod
    def _sub_user_input_for_dollar(replacement_text, user_input):
        user_input = '<span class="css-system-text-user-input">' + user_input + "</span>"
        return replacement_text.replace("$", user_input)

    # This method must remain functionally equal to ps2_create_script.js # addReplacementsForComponents
    # This is to ensure consistent server-side rendering of user-created powers.
    # DO NOT REFACTOR THIS METHOD WITHOUT CHANGING THE ASSOCIATED METHOD IN THE FE
    def _add_replacements_for_components(self, replacement_map, power):
        components = [
            self.system.blob[PowerSystem.MODALITIES][power.modality_id],
            self.system.blob[PowerSystem.EFFECTS][power.base_id],
            self.system.blob[PowerSystem.VECTORS][power.vector_id],
        ]
        for component in components:
            for sub in component["substitutions"]:
                marker = sub["marker"]
                replacement = sub["replacement"]
                new_sub = Substitution(sub["mode"], replacement)
                replacement_map[marker].append(new_sub)
        return replacement_map

    # This method must remain functionally equal to ps2_create_script.js # addReplacementsForParameters
    # This is to ensure consistent server-side rendering of user-created powers.
    # DO NOT REFACTOR THIS METHOD WITHOUT CHANGING THE ASSOCIATED METHOD IN THE FE
    def _add_replacements_for_parameters(self, replacements, param_instances):
        # param_instances already does not include disabled parameters (we lean on the FE for this)
        for param in param_instances:
            pow_param = param.relevant_power_param
            selection = pow_param.get_value_for_level(param.value)
            param_pk = pow_param.relevant_parameter_id
            blob_param = self.system.blob[PowerSystem.PARAMETERS][param_pk]
            subs = blob_param["substitutions"]
            if blob_param["render_lvl_zero"] or param.value > 0:
                for sub in subs:
                    marker = sub["marker"]
                    replacement = sub["replacement"]
                    if "$" in replacement:
                        replacement = replacement.replace("$", selection)
                    replacements[marker].append(Substitution(sub["mode"], replacement))
                replacements[param_pk + "-param-level"].append(Substitution(ADDITIVE, str(param.value)))
        return replacements

    # This method must remain functionally equal to ps2_create_script.js # addReplacementsForFields
    # This is to ensure consistent server-side rendering of user-created powers.
    # DO NOT REFACTOR THIS METHOD WITHOUT CHANGING THE ASSOCIATED METHOD IN THE FE
    def _add_replacements_for_fields(self, replacements, power, field_instances):
        # First we need to find the relevant fields in the power blob
        components = self.system.components_from_model(power.base_id, power.vector_id, power.modality_id)
        text_field_by_id = {}
        roll_field_by_id = {}
        for component in components:
            if "text_fields" in component:
                text_field_by_id.update({x["id"]: x for x in component["text_fields"]})
            if "roll_fields" in component:
                roll_field_by_id.update({x["id"]: x for x in component["roll_fields"]})

        # Now we do what the FE does
        for field in field_instances:
            if field.is_weapon():
                weap_replacements = self.system.blob[PowerSystem.WEAP_REPLACEMENTS_BY_PK][field.weapon_id]
                for repl in weap_replacements:
                    replacements[repl["marker"]].append(Substitution(repl["mode"], repl["replacement"]))
            else:
                sub = ""
                if field.is_text():
                    sub = field.value
                    blob_field = text_field_by_id[field.relevant_field_id]
                if field.is_roll():
                    blob_field = roll_field_by_id[field.relevant_field_id]
                    if field.relevant_field.caster_rolls:
                        sub = field.roll.render_ps2_html_for_current_contractor()
                    else:
                        sub = field.roll.render_value_for_ps2()
                replacement = blob_field["replacement"]
                if "$" in replacement:
                    if field.is_roll():
                        replacement = replacement.replace("$", sub)
                        replacement = "<span class=\"css-system-text-roll\">{}</span>".format(replacement)
                    else:
                        replacement = SystemTextRenderer._sub_user_input_for_dollar(replacement, sub)
                replacements[blob_field["marker"]].append(Substitution(ADDITIVE, replacement))
        return replacements

    def _collapse_substitutionss(self, replacements):
        # Normalizes lists of substitutions so that they follow the semantics associated with the replacement modes:
        # EPHEMERAL subs are replaced by all other types
        # UNIQUE subs replace all other types, leaving a single substitution.
        # ADDITIVE subs can exist in any quantity.
        # return a mapping of marker string to list of replacement texts.
        cleaned_replacements = defaultdict(list)
        for marker in replacements:
            substitutions = replacements[marker]
            if len(substitutions) == 0:
                raise ValueError("Empty subs for marker: " + marker)
            if len(substitutions) == 1:
                cleaned_replacements[marker] = [substitutions[0].replacement]
                continue
            unique_subs = [x for x in substitutions if x.mode == UNIQUE]
            if len(unique_subs) > 1:
                raise ValueError("Multiple subs are unique for marker:" + marker)
            if len(unique_subs) == 1:
                cleaned_replacements[marker] = [unique_subs[0].replacement]
                continue
            ephemeral_subs = [x for x in substitutions if x.mode == EPHEMERAL]
            non_ephemeral_subs = [x for x in substitutions if x.mode != EPHEMERAL]
            if len(ephemeral_subs) > 0 and len(non_ephemeral_subs) > 0:
                cleaned_replacements[marker] = [x.replacement for x in non_ephemeral_subs]
                continue
            if len(ephemeral_subs) > 1:
                cleaned_replacements[marker] = [ephemeral_subs[0].replacement]
                continue
            cleaned_replacements[marker] = [x.replacement for x in substitutions]
        for marker in cleaned_replacements:
            cleaned_replacements[marker] = [x for x in cleaned_replacements[marker] if len(x) > 0]
            if len(cleaned_replacements[marker]) == 0:
                cleaned_replacements[marker] = [""]
        return cleaned_replacements

    @staticmethod
    def _replace_in_system_text(system_text, replacement_map, to_replace):
        markers = to_replace.markers
        replacements = None
        for marker in markers:
            if marker in replacement_map:
                if not replacements:
                    replacements = []
                replacements.extend(replacement_map[marker])
        replacement_text = SystemTextRenderer._get_replacement_text(replacements, to_replace)
        return system_text[0: to_replace.start] + replacement_text + system_text[to_replace.end + 1:]

    @staticmethod
    def _get_replacement_text(replacements, to_replace):
        if not replacements:
            if to_replace.default_value:
                return to_replace.default_value
            else:
                return ""
        if to_replace.replacement_type == '#':
            return str(sum(replacements))
        replacements = [x for x in replacements if len(x) > 0]
        if len(replacements) == 0:
            return ""
        if to_replace.replacement_type == '{':
            replacements[0] = "</p><p>" + replacements[0]
        if to_replace.replacement_type == ';':
            replacements[0] = "<ul class=\"css-power-system-list\"><li>" + replacements[0]
            replacements[-1] = replacements[-1] + "</li></ul>"
        if len(replacements[0]) > 0 and to_replace.should_capitalize:
            replacements[0] = replacements[0][0].upper() + replacements[0][1:]
        if len(replacements) == 1:
            return replacements[0]
        if to_replace.replacement_type == '(':
            replacements[-1] = "and " + replacements[-1]
        if to_replace.replacement_type == '@':
            replacements[-1] = "or " + replacements[-1]
        join_string = SystemTextRenderer.paren_join_string[to_replace.replacement_type]
        if to_replace.replacement_type in ["@", "("] and len(replacements) == 2:
            join_string = " "
        return join_string.join(replacements)
