#!/usr/bin/python




import re

from optparse import OptionParser
try:
    from queue import *
except ImportError:
    from Queue import *
import io


try:
    import pygraphviz as pgv
except:
    print("Unable to import pygraphviz. Visualization is disabled.")
    import config

import pkg_resources as pr
import os
from os.path import join
import json

resource_package = __name__

ENTITY_TERM = "TERM"
ENTITY_TYPE_DEF = "TYPE_DEF"
ENTITY_EXCLUDED_TERM = "EXCLUDED_TERM"

VERBOSE = False

class Synonym:
    """
    Represents a synonym of a term. Stores both the
    synonym string and synonym type.
    """
    def __init__(self, syn_str, syn_type):
        self.syn_str = syn_str
        self.syn_type = syn_type

    def __repr__(self):
        return str((self.syn_str, self.syn_type))

class Term:
    def __init__(
            self,
            id,
            name,
            definition=None,
            synonyms=[],
            comment=None,
            xrefs=None,
            relationships={},
            property_values=[],
            subsets=[],
            namespace=None
        ):
        """
        Args:
            id: term identifier (e.g. 'CL:0000555')
            name: name of term
            definition: term definition
            synonyms: list of Synonym objects representing
                synonyms of the term
            comment: comment about the term
            xrefs: list of URIs of external definitions of
                this term
            relationships: a dictionary mapping a relationship
                type to term id's related to this term through
                that type
            namespace: a string denoting the term's namespace
        """
        self.id = id
        self.name = name
        self.definition = definition
        self.synonyms = synonyms
        self.comment = comment
        self.xrefs = xrefs
        self.relationships = relationships
        self.property_values = property_values
        self.subsets = subsets
        self.namespace = namespace

    def __repr__(self):
        rep = {
            "id":self.id,
            "name":self.name,
            "definition":self.definition,
            "synonyms": self.synonyms,
            "relationships": self.relationships,
            "subsets": self.subsets,
            "namespace": self.namespace
        }
        return str(rep)

    def is_a(self):
        return self.get_related_terms("is_a")

    def inv_is_a(self):
        return self.get_related_terms("inv_is_a")

    def get_related_terms(self, relation):
        if relation in self.relationships:
            return self.relationships[relation]
        else:
            return []

class OntologyGraph:
    def __init__(self, id_to_term,
        enriched_synonyms_file=None):
        self.id_to_term = id_to_term

    def subtype_names(self, supertype_name):
        id = self.name_to_ids[supertype_name]
        for t in self.id_to_term[id].inv_is_a():
            print(self.id_to_term[t].name)

    def graphviz(self, root_id=None):
        g = pgv.AGraph(directed='True')

        # Breadth-first traversal from root
        visited_ids = set()
        curr_id = root_id
        q = Queue()
        q.put(curr_id)
        while not q.empty():
            curr_id = q.get()
            visited_ids.add(curr_id)
            for sub_id in self.id_to_term[curr_id].inv_is_a():
                if not sub_id in visited_ids:
                    g.add_edge(self.id_to_term[curr_id].name,
                        self.id_to_term[sub_id].name)
                    q.put(sub_id)
        print(str(g))

    def direct_subterms(self, id):
        return set([
            self.id_to_term[x]
            for x in self.id_to_term[id].relationships["inv_is_a"]
        ])

    def recursive_subterms(self, id):
        return self.recursive_relationship(id, ["inv_is_a"])

    def recursive_superterms(self, id):
        return self.recursive_relationship(id, ["is_a"])

    def recursive_relationship(self, t_id, recurs_relationships):
        """
        To be used with caution?
        """
        if t_id not in self.id_to_term:
            return set()
        gathered_ids = set()
        curr_id = t_id
        q = Queue()
        q.put(curr_id)
        visited_ids = set()
        while not q.empty():
            curr_id = q.get()
            visited_ids.add(curr_id)
            gathered_ids.add(curr_id)
            for rel in recurs_relationships:
                if curr_id not in self.id_to_term:
                    continue
                if rel in self.id_to_term[curr_id].relationships:
                    for rel_id in self.id_to_term[curr_id].relationships[rel]:
                        if not rel_id in visited_ids:
                            q.put(rel_id)
        return gathered_ids


class MappableOntologyGraph(OntologyGraph):
    def empty_list(self):
        return []

    def __init__(self, id_to_term, nonmappable_terms):
        OntologyGraph.__init__(self, id_to_term)
        """
        Args:
            nonmappable_terms: collection of term IDs that cannot
                be mapped to
        """
        if not nonmappable_terms:
            self.nonmappable_terms = set()
        else:
            self.nonmappable_terms = set(nonmappable_terms)
        self.mappable_term_ids = set(self.id_to_term.keys()).difference(self.nonmappable_terms)

    def get_mappable_term_ids(self):
        return self.mappable_term_ids

    def get_mappable_terms(self):
        return [y
            for x,y in self.id_to_term.items()
            if x not in self.nonmappable_terms
        ]


def build_ontology(ont_to_loc, restrict_to_idspaces=None,
    include_obsolete=False, restrict_to_roots=None,
    exclude_terms=None):

    og = parse_obos(ont_to_loc,
        restrict_to_idspaces=restrict_to_idspaces,
        include_obsolete=include_obsolete)

    # Add enriched synonyms
    cvcl_syns_f = pr.resource_filename(
        resource_package,
        join("metadata", "term_to_extra_synonyms.json")
    )
    term_to_syns = None
    with open(cvcl_syns_f, "r") as f:
        term_to_syns = json.load(f)
    for term in og.id_to_term.values():
        if term.id in term_to_syns:
            for syn in term_to_syns[term.id]:
                term.synonyms.add(Synonym(syn, "ENRICHED"))

    # Remove specified synonyms
    term_to_remove_syns_f = pr.resource_filename(
        resource_package,
        join("metadata", "term_to_remove_synonyms.json")
    )
    term_remove_syns = None
    with open(term_to_remove_syns_f, "r") as f:
        term_remove_syns = json.load(f)
    for t_id, rem_syn_data in term_remove_syns.items():
        if t_id in og.id_to_term:
            exclude_syns = set(rem_syn_data["exclude_synonyms"])
            term = og.id_to_term[t_id]
            term.synonyms = [
                x
                for x in term.synonyms
                if x.syn_str not in exclude_syns
            ]

    if restrict_to_roots:
        keep_ids = set() # The IDs that we will keep

        # Get the subterms of terms that we want to keep
        for root_id in restrict_to_roots:
            keep_ids.update(og.recursive_subterms(root_id))

        # Build the ontology-graph object
        id_to_term = {}
        for t_id in keep_ids:
            t_name = og.id_to_term[t_id].name
            id_to_term[t_id] =  og.id_to_term[t_id]

            # Update the relationships between terms to remove dangling edges
            for rel, rel_ids in og.id_to_term[t_id].relationships.items():
                og.id_to_term[t_id].relationships[rel] = [
                    x
                    for x in rel_ids
                    if x in keep_ids
                ]

        #return OntologyGraph(id_to_term)
        return MappableOntologyGraph(id_to_term, exclude_terms)
    else:
        return MappableOntologyGraph(og.id_to_term, exclude_terms)


def most_specific_terms(term_ids, og, sup_relations=["is_a"]):
    """
    Given a set of terms S, this method returns all terms that
    have no children in S.
    Args:
        og: the ontology graph object
        sup_relations: the relationship types through which
            to define children
    """
    term_ids = set([x for x in term_ids if x in og.id_to_term])

    if len(term_ids) < 1:
        return term_ids

    terms = [og.id_to_term[x] for x in term_ids]
    most_specific_terms = []
    # Map terms to superterms
    term_id_to_superterm_ids = {}
    for term in terms:
        term_id_to_superterm_ids[term.id] = og.recursive_relationship(term.id, sup_relations)

    # Create "more-general-than" tree
    have_relations = set()
    more_general_than = {}
    for term_a in term_id_to_superterm_ids.keys():
        for term_b, b_superterms in term_id_to_superterm_ids.items():
            if term_a == term_b:
                continue
            if term_a in b_superterms:
                if not term_a in more_general_than.keys():
                    more_general_than[term_a] = []
                more_general_than[term_a].append(term_b)
                have_relations.update([term_a, term_b])

    # Collect leaves of the tree
    for subs in more_general_than.values():
        for s in subs:
            if not s in more_general_than.keys():
                most_specific_terms.append(s)
    return list(set(most_specific_terms + list(set(term_ids) - have_relations))) # TODO Clean this up


def parse_obos(ont_to_loc, restrict_to_idspaces=None, include_obsolete=False):

    def add_inverse_relationship_to_parents(term, relation, inverse_relation):
        for sup_term_id in [x for x in term.get_related_terms(relation)]:
            if sup_term_id in id_to_term:
                sup_term = id_to_term[sup_term_id]
                if inverse_relation not in sup_term.relationships:
                    sup_term.relationships[inverse_relation] = []
                sup_term.relationships[inverse_relation].append(term.id)
            else:
                if VERBOSE:
                    print("Warning! Attempted to create inverse edge in term %s. \
                        Not found in not in the ontology" % sup_term_id)
                # Remove superterm from term's relationship list because it
                # is not in the current ontology
                while sup_term_id in term.relationships[relation]:
                    term.relationships[relation].remove(sup_term_id)
                if not term.relationships[relation]:
                    del term.relationships[relation]


    id_to_term = {}
    name_to_ids = {}

    # Iterate through OBO files and build up the ontology
    for ont, loc in ont_to_loc.items():
        i_to_t, n_to_is = parse_obo(loc,
            restrict_to_idspaces=restrict_to_idspaces,
            include_obsolete=include_obsolete)
        id_to_term.update(i_to_t)
        for name, ids in n_to_is.items():
            if name not in name_to_ids:
                name_to_ids[name] = ids
            else:
                name_to_ids[name].update(ids)

    for term in id_to_term.values():
        add_inverse_relationship_to_parents(term, "is_a", "inv_is_a")
        add_inverse_relationship_to_parents(term, "part_of", "inv_part_of")

    #return OntologyGraph(id_to_term, name_to_ids)
    return OntologyGraph(id_to_term)

def parse_obo(obo_file, restrict_to_idspaces=None, include_obsolete=False):
    """
    Parse OBO file.
    Args:
        obo_file: file path to OBO file
        restrict_to_idspaces: list of ID prefixes for which terms in that ID
            space should be included in the ontology. For example, if ['UBERON']
            is supplied, then only terms with IDs of the form 'UBERON:XXXXX'
            will be included in the ontology. If this argument is None, then all
            terms  will be included.
    """

    def process_chunk_of_lines(curr_lines, restrict_to_idspaces,
        name_to_ids, id_to_term):
        entity = parse_entity(curr_lines, restrict_to_idspaces)
        if not entity:
            if VERBOSE:
                print("ERROR!")
        elif entity[0] == ENTITY_TERM:
            term = entity[1]
            is_obsolete = entity[2]
            if not is_obsolete or include_obsolete:
                id_to_term[term.id] = term
                if term.name not in name_to_ids:
                    name_to_ids[term.name]= set()
                name_to_ids[term.name].add(term.id)

    def add_inverse_relationship_to_parents(term, relation, inverse_relation):
        for sup_term_id in [x for x in term.get_related_terms(relation)]:
            if sup_term_id in id_to_term:
                sup_term = id_to_term[sup_term_id]
                if inverse_relation not in sup_term.relationships:
                    sup_term.relationships[inverse_relation] = []
                sup_term.relationships[inverse_relation].append(term.id)
            else:
                if VERBOSE:
                    print("Warning! Attempted to create inverse edge in term %s. \
                        Not found in not in the ontology" % sup_term_id)
                # Remove superterm from term's relationship list because it
                # is not in the current ontology
                while sup_term_id in term.relationships[relation]:
                    term.relationships[relation].remove(sup_term_id)
                if not term.relationships[relation]:
                    del term.relationships[relation]


    header_info = {}
    print("Loading ontology from %s ..." % obo_file)
    name_to_ids = {}
    id_to_term = {}
    with io.open(obo_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                break # Reached end of header
            header_info[line.split(":")[0].strip()] = ":".join(line.split(":")[1:]).strip()

        curr_lines = []
        for line in f:
            if not line.strip():
                if not curr_lines: # nothing has been read yet
                    continue
                process_chunk_of_lines(curr_lines, restrict_to_idspaces,
                    name_to_ids, id_to_term)
                curr_lines = []
            else:
                curr_lines.append(line)
        if curr_lines: # process last chunk of lines at bottom of file
            process_chunk_of_lines(curr_lines, restrict_to_idspaces,
                name_to_ids, id_to_term)

        # Create inverse "is_a" and "part_of" edges between terms
        #for term in id_to_term.values():
        #    add_inverse_relationship_to_parents(term, "is_a", "inv_is_a")
        #    add_inverse_relationship_to_parents(term, "part_of", "inv_part_of")

    return id_to_term, name_to_ids



def parse_entity(lines, restrict_to_idspaces):
    def parse_term_attrs(lines):
        attrs = {}
        for line in lines:
            tokens = line.split(":")
            if not tokens[0].strip() in attrs.keys():
                attrs[tokens[0].strip()] = []
            attrs[tokens[0].strip()].append(":".join(tokens[1:]).strip())
        return attrs

    def parse_relationships(attrs):
        """
        Extract the relationships of this term to other terms.
        Returns:
            A dictionary mapping a relationship type to the set
            of term ids for which this term relates to through
            said type.
        """
        relationships = {}
        # 'is_a' relationship
        is_a = [
            x.split("!")[0].split()[0].strip() for x in attrs["is_a"]] if "is_a" in attrs else set()
        if restrict_to_idspaces:
            is_a = [x for x in is_a if x.split(":")[0] in restrict_to_idspaces]
        if len(is_a) > 0: # Always add 'is_a' relationship
            relationships["is_a"] = []
            for is_a_t in is_a:
                relationships["is_a"].append(is_a_t)

        # Non-'is_a' relationships
        if "relationship" in attrs:
            for rel_raw in attrs["relationship"]:
                rel = rel_raw.split()[0]
                rel_term_id = rel_raw.split()[1]
                if rel not in relationships:
                    relationships[rel] = []
                relationships[rel].append(rel_term_id)

        return relationships

    def extract_synonyms(raw_syns):
        """
        Args:
            raw_syns: all of the lines of the OBO file corresponding to synonyms
                of a given term.
        Returns:
            A set of tuples where the first element is the synonym string and
            the second element is the synonym type (e.g. 'EXACT' or 'NARROW')
        """
        synonyms = set()
        for syn in raw_syns:
            m = re.search('\".+\"', syn)
            if m:
                syn_type = syn.split('"')[2].strip().split()[0]
                parsed_syn = m.group(0)[1:-1].strip()
                synonyms.add(Synonym(parsed_syn, syn_type))
        return synonyms

    def extract_xrefs(raw_xrefs):
        xrefs = set()
        for xref in raw_xrefs:
            xrefs.add(xref.split("!")[0].strip())
        return list(xrefs)

    def is_include_term(attrs):
        if restrict_to_idspaces:
            term_prefix = attrs["id"][0].split(":")[0]
            if term_prefix in restrict_to_idspaces:
                return True
            else:
                return False
        else:
            return True

    def parse_is_obsolete(attrs):
        """
        Check if "is_obsolete: true" is included in the term.
        If so, this term is obsolete.
        """
        is_obsolete = False
        if "is_obsolete" in attrs:
            is_obsolete = True if attrs["is_obsolete"][0] == "true" else False
        return is_obsolete

    def parse_synonyms(attrs):
        return extract_synonyms(attrs["synonym"]) if "synonym" in attrs.keys() else set()

    def parse_definition(attrs):
        return attrs["def"][0] if "def" in attrs.keys() else None

    def parse_xrefs(attrs):
        xrefs = []
        if "xref" in attrs:
            xrefs = extract_xrefs(attrs["xref"])
        return xrefs

    def extract_property_values(raw_prop_vals):
        prop_vals = set()
        for prop_val in raw_prop_vals:
            if "\"" in prop_val:
                m = re.search('\".+\"', prop_val)
                if m:
                    prop = prop_val.split('"')[0].strip()
                    val = m.group(0)[1:-1].strip()
            else:
                prop = prop_val.split()[0].strip()
                val = prop_val.split()[1].strip()
            prop_vals.add((prop, val))
        return prop_vals

    def parse_subsets(attrs):
        if "subset" in attrs:
            return set(attrs["subset"])
        return set()

    def parse_namespace(attrs):
        return attrs["namespace"][0] if "namespace" in attrs.keys() else None

    def parse_property_values(attrs):
        return extract_property_values(attrs["property_value"]) if "property_value" in attrs.keys() else set()

    def parse_comment(attrs):
        if "comment" in attrs:
            return attrs["comment"][0]
        return None

    def is_valid_term(attrs):
        if "name" not in attrs:
            return False
        return True


    if lines[0].strip() == "[Term]":
        attrs = parse_term_attrs(lines)

        if not is_include_term(attrs):
            return (ENTITY_EXCLUDED_TERM, None)

        if not is_valid_term(attrs):
            return ("ERROR PARSING ENTITY", None)

        definition = parse_definition(attrs)
        synonyms = parse_synonyms(attrs)
        is_obsolete = parse_is_obsolete(attrs)
        xrefs = parse_xrefs(attrs)
        comment = parse_comment(attrs)
        relationships = parse_relationships(attrs)
        property_values = parse_property_values(attrs)
        subsets = parse_subsets(attrs)
        namespace = parse_namespace(attrs)

        # Build term
        term = Term(
            attrs["id"][0],
            attrs["name"][0].strip(),
            definition=definition,
            synonyms=set(synonyms),
            xrefs=xrefs,
            relationships=relationships,
            property_values=property_values,
            comment=comment,
            subsets=subsets,
            namespace=namespace
        )

        return (ENTITY_TERM, term, is_obsolete)

    elif lines[0].strip() == "[Typedef]": # TODO include type definitions at some point, if necesary
        return (ENTITY_TYPE_DEF, None, None)

    else:
        if VERBOSE:
            print("Unable to parse chunk: %s" % lines)
