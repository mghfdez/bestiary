#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2020 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from bestiary.core import db
from bestiary.core.context import BestiaryContext
from bestiary.core.errors import (AlreadyExistsError,
                                  NotFoundError)
from bestiary.core.log import TransactionsLog
from bestiary.core.models import (Ecosystem,
                                  Project,
                                  Transaction,
                                  Operation)


DUPLICATED_ECOSYSTEM_ERROR = "Ecosystem 'Example' already exists in the registry"
DUPLICATED_PROJECT_ERROR = "Project 'example' already exists in the registry"
NAME_NONE_ERROR = "'name' cannot be None"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
ECOSYSTEM_ID_NONE_ERROR = "AttributeError: 'NoneType' object has no attribute 'id'"
NAME_WHITESPACES_ERROR = "'name' cannot be composed by whitespaces only"
NAME_CONTAIN_WHITESPACES_ERROR = "'name' cannot contain whitespace characters"
NAME_VALUE_ERROR = "field 'name' value must be a string; int given"
TITLE_VALUE_ERROR = "field 'title' value must be a string; int given"
TITLE_EMPTY_ERROR = "'title' cannot be an empty string"
TITLE_WHITESPACES_ERROR = "'title' cannot be composed by whitespaces only"
DESC_EMPTY_ERROR = "'description' cannot be an empty string"
DESC_WHITESPACES_ERROR = "'description' cannot be composed by whitespaces only"
DESC_VALUE_ERROR = "field 'description' value must be a string; int given"
ECOSYSTEM_NOT_FOUND_ERROR = "Ecosystem ID 2 not found in the registry"
PROJECT_NOT_FOUND_ERROR = "Project ID 2 not found in the registry"
PROJECT_PARENT_EQUAL_ERROR = "Project 'example' cannot be added as parent project"

NAME_ALPHANUMERIC_ERROR = "'name' must start with an alphanumeric character"


class TestFindEcosystem(TestCase):
    """Unit tests for find_ecosystem"""

    def setUp(self):
        """Load initial dataset"""

        Ecosystem.objects.create(id=1,
                                 name='Example',
                                 title='Example title',
                                 description='Example description')

    def test_find_ecosystem(self):
        """Test if an ecosystem is found by its id"""

        eco = db.find_ecosystem(1)

        # Tests
        self.assertIsInstance(eco, Ecosystem)
        self.assertEqual(eco.id, 1)
        self.assertEqual(eco.name, 'Example')
        self.assertEqual(eco.title, 'Example title')
        self.assertEqual(eco.description, 'Example description')

    def test_ecosystem_not_found(self):
        """Test whether it raises an exception when the ecosystem is not found"""

        with self.assertRaisesRegex(NotFoundError, ECOSYSTEM_NOT_FOUND_ERROR):
            db.find_ecosystem(2)


class TestAddEcosystem(TestCase):
    """Unit tests for add_Ecosystem"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = BestiaryContext(self.user)

        self.trxl = TransactionsLog.open('add_ecosystem', self.ctx)

    def test_add_ecosystem(self):
        """Check if a new ecosystem is added"""

        name = 'example'
        title = 'Example title'
        desc = 'Example description'

        eco = db.add_ecosystem(self.trxl,
                               name,
                               title=title,
                               description=desc)
        self.assertIsInstance(eco, Ecosystem)
        self.assertEqual(eco.name, name)
        self.assertEqual(eco.title, title)
        self.assertEqual(eco.description, desc)

        eco_db = Ecosystem.objects.get(id=eco.id)
        self.assertIsInstance(eco_db, Ecosystem)
        self.assertEqual(eco_db.id, eco.id)
        self.assertEqual(eco_db.name, name)
        self.assertEqual(eco_db.title, title)
        self.assertEqual(eco_db.description, desc)

    def test_name_none(self):
        """Check whether ecosystems with None as name cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_NONE_ERROR):
            db.add_ecosystem(self.trxl,
                             None,
                             title='Example title',
                             description='Example desc.')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_empty(self):
        """Check whether ecosystems with empty names cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_EMPTY_ERROR):
            db.add_ecosystem(self.trxl,
                             '',
                             title='Example title',
                             description='Example desc.')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_whitespaces(self):
        """Check whether ecosystems containing whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_CONTAIN_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'my ecosystem',
                             title='Example title',
                             description='Example desc.')

        with self.assertRaisesRegex(ValueError, NAME_ALPHANUMERIC_ERROR):
            db.add_ecosystem(self.trxl,
                             ' ecosystem',
                             title='Example title',
                             description='Example desc.')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             '  ',
                             title='Example title',
                             description='Example desc.')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             '\t',
                             title='Example title',
                             description='Example desc.')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             ' \t  ',
                             title='Example title',
                             description='Example desc.')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_title_none(self):
        """Check whether ecosystems with None as title can be added"""

        eco = db.add_ecosystem(self.trxl,
                               'Example',
                               title=None,
                               description='Example desc.')

        self.assertIsInstance(eco, Ecosystem)
        self.assertEqual(eco.name, 'Example')
        self.assertEqual(eco.title, None)
        self.assertEqual(eco.description, 'Example desc.')

        eco = Ecosystem.objects.get(id=eco.id)
        self.assertIsInstance(eco, Ecosystem)
        self.assertEqual(eco.name, 'Example')
        self.assertEqual(eco.title, None)
        self.assertEqual(eco.description, 'Example desc.')

    def test_title_empty(self):
        """Check whether ecosystems with empty titles cannot be added"""

        with self.assertRaisesRegex(ValueError, TITLE_EMPTY_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='',
                             description='Example desc.')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_title_whitespaces(self):
        """Check whether ecosystem titles composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, TITLE_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='  ',
                             description='Example desc.')

        with self.assertRaisesRegex(ValueError, TITLE_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='\t',
                             description='Example desc.')

        with self.assertRaisesRegex(ValueError, TITLE_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title=' \t  ',
                             description='Example desc.')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_description_none(self):
        """Check whether ecosystems with None as description can be added"""

        eco = db.add_ecosystem(self.trxl,
                               'Example',
                               title='Example title',
                               description=None)

        self.assertIsInstance(eco, Ecosystem)
        self.assertEqual(eco.name, 'Example')
        self.assertEqual(eco.title, 'Example title')
        self.assertEqual(eco.description, None)

        eco = Ecosystem.objects.get(id=eco.id)
        self.assertIsInstance(eco, Ecosystem)
        self.assertEqual(eco.name, 'Example')
        self.assertEqual(eco.title, 'Example title')
        self.assertEqual(eco.description, None)

    def test_description_empty(self):
        """Check whether ecosystems with empty descriptions cannot be added"""

        with self.assertRaisesRegex(ValueError, DESC_EMPTY_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='Example title',
                             description='')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_description_whitespaces(self):
        """Check whether ecosystem descriptions composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, DESC_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='Example title',
                             description='  ')

        with self.assertRaisesRegex(ValueError, DESC_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='Example title',
                             description='\t')

        with self.assertRaisesRegex(ValueError, DESC_WHITESPACES_ERROR):
            db.add_ecosystem(self.trxl,
                             'Example',
                             title='Example title',
                             description=' \t  ')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether ecosystems with the same name cannot be inserted"""

        name = 'Example'
        title1 = 'Example title 1'
        title2 = 'Example title 2'
        desc1 = 'Example desc 1'
        desc2 = 'Example desc 2'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ECOSYSTEM_ERROR):
            db.add_ecosystem(self.trxl, name, title=title1, description=desc1)
            db.add_ecosystem(self.trxl, name, title=title2, description=desc2)

    def test_operations(self):
        """Check if the right operations are created when adding an ecosystem"""

        timestamp = datetime_utcnow()

        title = 'Example title'
        desc = 'Example description'
        db.add_ecosystem(self.trxl,
                         'Example',
                         title=title,
                         description=desc)

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'ecosystem')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'Example')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 3)
        self.assertEqual(op1_args['name'], 'Example')
        self.assertEqual(op1_args['title'], 'Example title')
        self.assertEqual(op1_args['description'], 'Example description')


class TestAddProject(TestCase):
    """Unit tests for add_project"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = BestiaryContext(self.user)

        self.trxl = TransactionsLog.open('add_project', self.ctx)

        self.eco = Ecosystem.objects.create(name='Eco-example')

    def test_add_project(self):
        """Check if a new project is added"""

        proj = db.add_project(self.trxl,
                              self.eco,
                              'example',
                              title='Project title')
        self.assertIsInstance(proj, Project)
        self.assertEqual(proj.ecosystem, self.eco)
        self.assertEqual(proj.name, 'example')
        self.assertEqual(proj.title, 'Project title')
        self.assertEqual(proj.parent_project, None)

        proj_db = Project.objects.get(id=proj.id)
        self.assertIsInstance(proj_db, Project)
        self.assertEqual(proj_db.id, proj.id)
        self.assertEqual(proj_db.ecosystem, proj.ecosystem)
        self.assertEqual(proj_db.name, 'example')
        self.assertEqual(proj_db.title, 'Project title')
        self.assertEqual(proj_db.parent_project, None)

    def test_name_none(self):
        """Check whether projects with None as name cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_NONE_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           None,
                           title='Project title')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_empty(self):
        """Check whether projects with empty names cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_EMPTY_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           '',
                           title='Project title')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_whitespaces(self):
        """Check whether projects containing whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_CONTAIN_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           'my project',
                           title='Project title')

        with self.assertRaisesRegex(ValueError, NAME_ALPHANUMERIC_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           ' project',
                           title='Project title')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           '  ',
                           title='Project title')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           '\t',
                           title='Project title')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           ' \t  ',
                           title='Project title')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_title_none(self):
        """Check whether projects with None as title can be added"""

        proj = db.add_project(self.trxl,
                              self.eco,
                              'example',
                              title=None)
        self.assertIsInstance(proj, Project)
        self.assertEqual(proj.ecosystem, self.eco)
        self.assertEqual(proj.name, 'example')
        self.assertEqual(proj.title, None)
        self.assertEqual(proj.parent_project, None)

        proj_db = Project.objects.get(id=proj.id)
        self.assertIsInstance(proj_db, Project)
        self.assertEqual(proj_db.ecosystem, proj.ecosystem)
        self.assertEqual(proj_db.id, proj.id)
        self.assertEqual(proj_db.name, 'example')
        self.assertEqual(proj_db.title, None)
        self.assertEqual(proj_db.parent_project, None)

    def test_title_empty(self):
        """Check whether projects with empty titles cannot be added"""

        with self.assertRaisesRegex(ValueError, TITLE_EMPTY_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           'example',
                           title='')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_title_whitespaces(self):
        """Check whether project titles composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, TITLE_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           'example',
                           title='  ')

        with self.assertRaisesRegex(ValueError, TITLE_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           'example',
                           title='\t')

        with self.assertRaisesRegex(ValueError, TITLE_WHITESPACES_ERROR):
            db.add_project(self.trxl,
                           self.eco,
                           'example',
                           title=' \t  ')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether projects with the same name cannot be inserted"""

        name = 'example'
        title1 = 'Project title 1'
        title2 = 'Project title 2'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_PROJECT_ERROR):
            db.add_project(self.trxl, self.eco, name, title=title1)
            db.add_project(self.trxl, self.eco, name, title=title2)

    def test_operations(self):
        """Check if the right operations are created when adding a project"""

        timestamp = datetime_utcnow()

        db.add_project(self.trxl,
                       self.eco,
                       'example',
                       title='Project title')

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'project')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'example')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 3)
        self.assertEqual(op1_args['name'], 'example')
        self.assertEqual(op1_args['title'], 'Project title')
        self.assertEqual(op1_args['ecosystem'], self.eco.id)


class TestDeleteEcosystem(TestCase):
    """Unit tests for delete_ecosystem"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = BestiaryContext(self.user)

        self.trxl = TransactionsLog.open('delete_ecosystem', self.ctx)

    def test_delete_ecosystem(self):
        """Check whether it deletes an ecosystem and its related data"""

        eco = Ecosystem.objects.create(id=1,
                                       name='Example',
                                       title='Example title',
                                       description='Example desc.')

        # Check data and remove ecosystem
        self.assertEqual(eco.id, 1)
        self.assertEqual(eco.name, 'Example')
        self.assertEqual(eco.title, 'Example title')
        self.assertEqual(eco.description, 'Example desc.')
        db.delete_ecosystem(self.trxl, eco)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Ecosystem.objects.get(id=1)

    def test_operations(self):
        """Check if the right operations are created when deleting an ecosystem"""

        timestamp = datetime_utcnow()
        eco = Ecosystem.objects.create(id=1,
                                       name='Example',
                                       title='Example title',
                                       description='Example desc.')

        transactions = Transaction.objects.filter(name='delete_ecosystem')
        trx = transactions[0]

        db.delete_ecosystem(self.trxl, eco)

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'ecosystem')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '1')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['id'], 1)


class TestUpdateEcosystem(TestCase):
    """Unit tests for update_ecosystem"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = BestiaryContext(self.user)

        self.trxl = TransactionsLog.open('update_ecosystem', self.ctx)

        self.ecosystem = Ecosystem.objects.create(id=1,
                                                  name='Example',
                                                  title='Example title',
                                                  description='Example desc.')

    def test_update_ecosystem(self):
        """Check if it updates an ecosystem"""

        eco_id = self.ecosystem.id
        args = {
            'name': 'Example-updated',
            'title': 'Example title updated',
            'description': 'Example desc. updated'
        }
        up_ecosystem = db.update_ecosystem(self.trxl, self.ecosystem, **args)

        # Tests
        self.assertIsInstance(up_ecosystem, Ecosystem)
        self.assertEqual(self.ecosystem, up_ecosystem)

        self.assertEqual(up_ecosystem.name, 'Example-updated')
        self.assertEqual(up_ecosystem.title, 'Example title updated')
        self.assertEqual(up_ecosystem.description, 'Example desc. updated')
        self.assertEqual(up_ecosystem.id, eco_id)

        # Check database object
        ecosystem_db = Ecosystem.objects.get(name='Example-updated')
        self.assertEqual(up_ecosystem, ecosystem_db)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime_utcnow()
        args = {
            'name': 'Example-updated',
            'title': 'Example title updated',
            'description': 'Example desc. updated'
        }
        db.update_ecosystem(self.trxl, self.ecosystem, **args)
        after_dt = datetime_utcnow()

        # Tests
        ecosystem = Ecosystem.objects.get(id=1)
        self.assertLessEqual(before_dt, ecosystem.last_modified)
        self.assertGreaterEqual(after_dt, ecosystem.last_modified)

    def test_name_empty(self):
        """Check if it fails when name is set to None when an empty string is given"""

        args = {'name': ''}
        with self.assertRaisesRegex(ValueError, ''):
            db.update_ecosystem(self.trxl, self.ecosystem, **args)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_invalid_type(self):
        """Check type values of name parameter"""

        args = {'name': 12345}
        with self.assertRaisesRegex(TypeError, NAME_VALUE_ERROR):
            db.update_ecosystem(self.trxl, self.ecosystem, **args)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_title_empty(self):
        """Check if the title is set to None when an empty string is given"""

        args = {'title': ''}
        up_ecosystem = db.update_ecosystem(self.trxl, self.ecosystem, **args)
        self.assertEqual(up_ecosystem.name, 'Example')
        self.assertEqual(up_ecosystem.title, None)
        self.assertEqual(up_ecosystem.description, 'Example desc.')

    def test_title_invalid_type(self):
        """Check type values of title parameter"""

        args = {'title': 12345}
        with self.assertRaisesRegex(TypeError, TITLE_VALUE_ERROR):
            db.update_ecosystem(self.trxl, self.ecosystem, **args)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_desc_empty(self):
        """Check if the description is set to None when an empty string is given"""

        args = {'description': ''}
        up_ecosystem = db.update_ecosystem(self.trxl, self.ecosystem, **args)
        self.assertEqual(up_ecosystem.name, 'Example')
        self.assertEqual(up_ecosystem.title, 'Example title')
        self.assertEqual(up_ecosystem.description, None)

    def test_desc_invalid_type(self):
        """Check type values of description parameter"""

        args = {'description': 12345}
        with self.assertRaisesRegex(TypeError, DESC_VALUE_ERROR):
            db.update_ecosystem(self.trxl, self.ecosystem, **args)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_operations(self):
        """Check if the right operations are created when updating an ecosystem"""

        timestamp = datetime_utcnow()

        # Update the ecosystem
        args = {
            'name': 'Example-updated',
            'title': 'Example title updated',
            'description': 'Example desc. updated'
        }
        db.update_ecosystem(self.trxl, self.ecosystem, **args)

        transactions = Transaction.objects.filter(name='update_ecosystem')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'ecosystem')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, str(self.ecosystem.id))
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 4)
        self.assertEqual(op1_args['id'], self.ecosystem.id)
        self.assertEqual(op1_args['name'], 'Example-updated')
        self.assertEqual(op1_args['title'], 'Example title updated')
        self.assertEqual(op1_args['description'], 'Example desc. updated')