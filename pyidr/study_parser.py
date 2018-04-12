#! /usr/bin/env python

import logging
import os
import re
import sys

logging.basicConfig(level=int(os.environ.get("DEBUG", logging.INFO)))

TYPES = ["Experiment", "Screen"]
MANDATORY_STUDY_KEYS = [
    'Comment\[IDR Study Accession\]',
    'Study Title',
    'Study Description',
    'Study Type',
    'Study Publication Title',
    'Study Author List',
]
OPTIONAL_STUDY_KEYS = [
    'Study Organism',
    'Study Publication Preprint',
    'Study PubMed ID',
    'Study PMC ID',
    'Study DOI',
    'Study Copyright',
    'Study License',
    'Study License URL',
    'Study Data Publisher',
    'Study Data DOI',
    'Study Experiments Number',
    'Study Screens Number',
]
MANDATORY_EXPERIMENT_KEYS = [
    'Comment\[IDR Experiment Name\]',
    'Experiment Description',
    'Experiment Imaging Method',
]
OPTIONAL_EXPERIMENT_KEYS = [
    'Experiment Data DOI',
    "Experiment Data Publisher",
]

MANDATORY_SCREEN_KEYS = [
    'Comment\[IDR Screen Name\]',
    'Screen Description',
    'Screen Imaging Method',
    'Screen Number',
    'Screen Type',
]
OPTIONAL_SCREEN_KEYS = [
    'Screen Data DOI',
    "Screen Data Publisher",
    'Screen Technology',
]


class StudyParser():

    def __init__(self, s):
        self._study_file = s
        self.study = self.parse(MANDATORY_STUDY_KEYS, OPTIONAL_STUDY_KEYS)
        self.experiments = []
        self.screens = []
        if 'Study Experiments Number' in self.study:
            self.parse_experiments()
        if 'Study Screens Number' in self.study:
            self.parse_screens()

    def get_value(self, key, expr=".*", fail_on_missing=True, lines=None):
        pattern = re.compile("^%s\t(%s)" % (key, expr))
        if not lines:
            lines = self._study_file
        for line in lines:
            m = pattern.match(line)
            if m:
                return m.group(1).rstrip()
        if fail_on_missing:
            raise Exception("Could not find value for key %s " % key)

    def parse(self, mandatory_keys, optional_keys, lines=None):
        d = {}
        for key in mandatory_keys:
            d[key] = self.get_value(key, lines=lines)
        for key in optional_keys:
            value = self.get_value(key, fail_on_missing=False, lines=lines)
            if value:
                d[key] = value
        return d

    def parse_experiments(self):
        n = int(self.study['Study Experiments Number'])
        self.experiments = [{}] * n

        for i in range(len(self.experiments)):
            logging.debug("Parsing experiment %g" % (i + 1))
            self.experiments[i] = self.parse(
                MANDATORY_EXPERIMENT_KEYS, OPTIONAL_EXPERIMENT_KEYS,
                lines=self.get_lines(i + 1, "Experiment"))
            self.experiments[i].update(self.study)

    def parse_screens(self):
        n = int(self.study['Study Screens Number'])
        self.screens = [{}] * n

        for i in range(len(self.screens)):
            logging.debug("Parsing screen %g" % (i + 1))
            self.screens[i] = self.parse(
                MANDATORY_SCREEN_KEYS, OPTIONAL_SCREEN_KEYS,
                lines=self.get_lines(i + 1, "Screen"))
            self.screens[i].update(self.study)

    def get_lines(self, index, component_type):
        PATTERN = re.compile("^%s Number\t(\d+)" % component_type)
        found = False
        lines = []
        for line in self._study_file:
            m = PATTERN.match(line)
            if m:
                if int(m.group(1)) == index:
                    found = True
                elif int(m.group(1)) != index and found:
                    return lines
            if found:
                lines.append(line)
        if not lines:
            raise Exception("Could not find %s %g" % (component_type, index))
        return lines


class Object():

    DESCRIPTION = (
        "Publication Title\n%(Study Publication Title)s\n\n"
        "Study Description\n%(Study Description)s")
    MAP_PAIRS = [
        ('Study Type', "%(Study Type)s"),
        ('Organism', "%(Study Organism)s"),
        ('Publication Title', "%(Study Publication Title)s"),
        ('Publication Authors', "%(Study Author List)s"),
        ('Pubmed ID', "%(Study PubMed ID)s "
         "https://www.ncbi.nlm.nih.gov/pubmed/%(Study PubMed ID)s"),
        ('PMC ID', "%(Study PMC ID)s"),
        ('Publication DOI', "%(Study DOI)s https://dx.doi.org/%(Study DOI)s"),
        ('License', "%(Study License)s %(Study License URL)s"),
        ('Copyright', "%(Study Copyright)s"),
        ('Data Publisher', "%(Study Data Publisher)s"),
        ('Data DOI', "%(Study Data DOI)s "
         "https://dx.doi.org/%(Study Data DOI)s"),
        ]

    def __init__(self, study):
        self.name = self.generate_description(study)
        self.description = self.generate_description(study)
        self.map = self.generate_annotation(study)

    def generate_description(self, study):
        return self.DESCRIPTION % study

    def generate_annotation(self, study):

        s = []
        for key, formatter in self.MAP_PAIRS:
            try:
                s.append(('%s' % key, formatter % study))
            except KeyError, e:
                logging.debug("Missing %s" % e.message)
        return s


class ScreenObject():

    DESCRIPTION = (
        "Publication Title\n%(Study Publication Title)s\n\n"
        "Screen Description\n%(Screen Description)s")

    def __init__(self, study):
        self.name = self.generate_description(study)
        self.description = self.generate_description(study)
        self.map = self.generate_annotation(study)


class Experiment():

    DESCRIPTION = (
        "Publication Title\n%(Study Publication Title)s\n\n"
        "Experiment Description\n%(Experiment Description)s")
    MAP_PAIRS = [
        ('Study Type', "%(Study Type)s"),
        ('Organism', "%(Study Organism)s"),
        ('Publication Title', "%(Study Publication Title)s"),
        ('Publication Authors', "%(Study Author List)s"),
        ('Pubmed ID', "%(Study PubMed ID)s "
         "https://www.ncbi.nlm.nih.gov/pubmed/%(Study PubMed ID)s"),
        ('PMC ID', "%(Study PMC ID)s"),
        ('Publication DOI', "%(Study DOI)s https://dx.doi.org/%(Study DOI)s"),
        ('License', "%(Study License)s %(Study License URL)s"),
        ('Copyright', "%(Study Copyright)s"),
        ('Data Publisher', "%(Study Data Publisher)s"),
        ('Data DOI', "%(Study Data DOI)s "
         "https://dx.doi.org/%(Study Data DOI)s"),
        ]

    def __init__(self, experiment):
        self.name =  "%(Comment\[IDR Experiment Name\])s" % experiment
        self.description = self.generate_description(experiment)
        self.map = self.generate_annotation(experiment)

    def generate_description(self, experiment):
        return self.DESCRIPTION % experiment

    def generate_annotation(self, experiment):

        s = []
        for key, formatter in self.MAP_PAIRS:
            try:
                s.append(('%s' % key, formatter % experiment))
            except KeyError, e:
                logging.debug("Missing %s" % e.message)
        return s


if __name__ == "__main__":
    if len(sys.argv) == 0:
        raise Exception("Requires one study file as an input")
    logging.info("Parsing %s" % sys.argv[1])
    with open(sys.argv[1], 'r') as f:
        parser = StudyParser(f.readlines())
    if len(sys.argv) == 3 and sys.argv[2] == '--report':
        for e in parser.experiments:
            obj = Experiment(e)
            print "name:\n%s\n" % obj.name
            print "description:\n%s\n" % obj.description
            print "map:\n%s\n" % obj.map
