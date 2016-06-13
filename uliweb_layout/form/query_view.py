#coding=utf8
# 用于定义查询条件
# 主要分为:
#   QueryView 只用来生成查询Form及校验,不与Model, Table相关联
#   QueryTableView 根据Table来生成QueryView
#   QueryModelView 根据Model来生成QueryView

from uliweb import functions
from uliweb.i18n import gettext_lazy as _
from uliweb.form import *
import logging

log = logging.getLogger(__name__)

class QueryViewError(Exception):pass

class QueryView(object):
    def __init__(self, data=None, fields=None,
                form_cls=None,
                form_args=None,
                post_created_form=None,
                layout=None, get_form_field=None):

        self.data = data or {}
        self.get_form_field = get_form_field
        self.result = {}

        self.form = None
        self.fields = self.get_fields(fields)
        self.form_cls = form_cls or functions.get_form('QueryForm')
        self.form_args = form_args or {}
        self.post_created_form = post_created_form

        #add layout support
        self.layout = layout
        self.make_form()
        self.run()

    def get_fields(self, fields):
        s = []
        for f in fields:
            if isinstance(f, (tuple, list)) and isinstance(f[1], BaseField):
                f[1].name = f[0]
                d = f[1].to_json()
                s.append(d)
            elif isinstance(f, dict):
                s.append(f)
            else:
                raise QueryViewError("Form field data format {!r} is not support, should"
                                    "be ('name', Field) or {}".format(f))
        self.fields = s
        return self.fields

    def get_layout(self):
        if self.layout:
            return self.layout

        layout = []
        for x in self.fields:
            if isinstance(x, str):
                layout.append(x)
            elif isinstance(x, (tuple, list)):
                layout.append(x[0])
            else:
                layout.append(x['name'])
        self.layout = [tuple(layout)]
        return self.layout

    def make_form(self):
        import uliweb.form as form

        if self.form_cls:
            class DummyForm(self.form_cls):
                pass
        else:
            class DummyForm(form.Form):
                pass

        #add layout support
        layout = self.get_layout()
        DummyForm.layout = layout

        for f in self.fields:
            flag = False
            if self.get_form_field:
                field = self.get_form_field(f['name'])
                if field:
                    flag = True
            if not flag:
                #maybe format is ('name', Field)
                if isinstance(f, (tuple, list)):
                    field = f[1]
                    f = {'name':f[0]}
                elif isinstance(f, dict):
                    field = make_field(**f)
                else:
                    raise QueryViewError("Form field data format {!r} is not support, should"
                                    "be ('name', Field) or {}".format(f))
            if field:
                DummyForm.add_field(f['name'], field, True)

        if self.post_created_form:
            self.post_created_form(DummyForm)

        self.form = DummyForm(data=self.data, **self.form_args)
        return self.form

    def run(self):
        from uliweb import request

        if not self.form:
            self.form = self.make_form()

        flag = self.form.validate(request.values)
        if flag:
            if self.data:
                for k, v in self.data.items():
                    if not self.form.data.get(k):
                        self.form.data[k] = v
            self.result = self.form.data.copy()
        else:
            self.result = self.form.data
        return self.result


    def get_json(self):
        return {
            'fields':self.fields,
            'layout':self.get_layout(),
            'data':self.result or self.data,
            'rules':self.form.front_rules['rules'],
            'messages':self.form.front_rules['messages'],
        }

property_mapping = {
    'BooleanProperty':'bool',
    'DateProperty':'date',
    'DateTimeProperty':'datetime',
    'TimeProperty':'time',
    'DecimalProperty':'float',
    'FloatProperty':'float',
    'IntegerProperty':'int',
    'StringProperty':'str',
    'CharProperty':'str',
    'TextProperty':'text',
    'UnicodeProperty':'unicode',
    #'Reference', 'ReferenceProperty',
    'BigIntegerProperty':'int',
    'FileProperty':'file',
    'UUIDBinaryProperty':'str',
    'UUIDProperty':'str',
    #'SelfReference', 'SelfReferenceProperty', 'OneToOne', 'ManyToMany',

}

def convert_property_to_json(name, property, default=None):
    default = default or {}
    prop_name = property.__class__.__name__
    d = {}
    d['name'] = name
    d['type'] = property_mapping.get(prop_name, 'str')
    d['label'] = property.verbose_name or name
    d.update(default)
    return d

class QueryModelView(QueryView):
    def __init__(self, model, **kwargs):
        self.model = functions.get_model(model)
        super(QueryModelView, self).__init__(**kwargs)

    def get_fields(self, fields):
        s = []
        for f in fields:
            if isinstance(f, (tuple, list)) and isinstance(f[1], BaseField):
                f[1].name = f[0]
                d = f[1].to_json()
                s.append(d)
            elif isinstance(f, dict):
                p = self.model.properties.get(f['name'])
                if p:
                    s.append(convert_property_to_json(f['name'], p, f))
                else:
                    s.append(f)
            elif isinstance(f, (str, unicode)):
                p = self.model.properties[f]
                s.append(convert_property_to_json(f, p))
            else:
                raise QueryViewError("Form field data format {!r} is not support, should"
                                    "be ('name', Field) or {}".format(f))
        self.fields = s
        return self.fields

    def _make_like(self, column, format, value):
        """
        make like condition
        :param column: column object
        :param format: '%_' '_%' '%_%'
        :param value: column value
        :return: condition object
        """
        c = []
        if format.startswith('%'):
            c.append('%')
        c.append(value)
        if format.endswith('%'):
            c.append('%')
        return column.like(''.join(c))

    def _make_op(self, column, op, value):
        """
        make op condition
        :param column: column object
        :param op: gt >, lt <, ge >=, ne !=, le <=, eq ==, in in_,
        :param value: volumn value
        :return: condition object
        """
        if not op:
            return None
        if op == '>':
            return column>value
        elif op == '<':
            return column<value
        elif op == '>=':
            return column>=value
        elif op == '<=':
            return column<=value
        elif op == '==':
            return column==value
        elif op == '!=':
            return column!=value
        elif op == 'in':
            return column.in_(value)
        else:
            raise KeyError('Not support this op[%s] value' % op)

    def get_condition(self, values=None):
        from sqlalchemy import true, and_

        values = values or self.result
        condition = true()
        model = self.model

        for v in self.fields:
            if isinstance(v, (tuple, list)):
                v = {'name':v[0]}
            elif not isinstance(v, dict):
                v = {'name':v}
            name = v['name']
            if name in values:
                render = v.get('render')
                value = values[name]
                if not value:
                    continue
                _cond = None
                if render:
                    _cond = render(model, name, value, values)
                else:
                    column = model.c.get(name)
                    if not column:
                        continue
                    if 'like' in v:
                        _cond = self._make_like(column, v['like'], value)
                    elif 'op' in v:
                        _cond = self._make_op(column, v['op'], value)
                    else:
                        if isinstance(value, (tuple, list)):
                            _cond = column.in_(value)
                        else:
                            _cond = column==value
                if _cond is not None:
                    condition = and_(_cond, condition)

        log.debug("condition=%s", condition)
        return condition