import random
from jinja2 import Template

__author__ = 'one'

from openerp import models, fields, api, _


class Assets(models.Model):
    _name = 'builder.website.asset'

    _rec_name = 'attr_id'
    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    attr_name = fields.Char(string='Name')
    attr_id = fields.Char(string='XML ID', required=True)
    attr_active = fields.Boolean('Active')
    attr_customize_show = fields.Boolean('Customize Show')
    attr_inherit_id = fields.Char('Inherit Asset')
    attr_priority = fields.Integer('Priority', default=10)
    type = fields.Selection([
                                ('website.theme', 'website.theme'),
                                ('website.assets_editor', 'website.assets_editor'),
                                ('website.assets_frontend', 'website.assets_frontend'),
                                ('website.assets_backend', 'website.assets_backend'),
    ], 'Type', required=True)

    # file_ids = fields.Many2many('builder.data.file', 'builder_website_asset_item', 'asset_id', 'file_id', 'Resources')
    item_ids = fields.One2many('builder.website.asset.item', 'asset_id', 'Items')

    @api.onchange('type')
    def onchange_type(self):
        if self.type in ['website.theme']:
            self.attr_customize_show = True
            self.attr_customize_show = False


class AssetItem(models.Model):
    _name = 'builder.website.asset.item'

    sequence = fields.Integer('Sequence', default=10)
    file_id = fields.Many2one('builder.data.file', 'File', ondelete='CASCADE')
    asset_id = fields.Many2one('builder.website.asset', 'Asset', ondelete='CASCADE')


class Pages(models.Model):
    _name = 'builder.website.page'

    _rec_name = 'attr_name'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    attr_name = fields.Char(string='Name', required=True)
    attr_id = fields.Char('XML ID', required=True)
    attr_inherit_id = fields.Char('Inherit Asset')
    attr_priority = fields.Integer('Priority', default=10)
    attr_page = fields.Boolean('Page', default=True)
    wrap_layout = fields.Selection([
        ('website.layout', 'website.layout'),
        ('web.login_layout', 'web.login_layout'),
    ], default='website.layout')
    content = fields.Html('Body', sanitize=False)

    def action_edit_html(self, cr, uid, ids, context=None):
        if not len(ids) == 1:
            raise ValueError('One and only one ID allowed for this action')
        url = '/builder/page/designer?model={model}&res_id={id}&enable_editor=1'.format (id = ids[0], model=self._name)
        return {
            'name': _('Edit Template'),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

class Theme(models.Model):
    _name = 'builder.website.theme'

    _rec_name = 'attr_name'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    attr_name = fields.Char(string='Name', required=True)
    attr_description = fields.Html('Description')
    asset_id = fields.Many2one('builder.website.asset', 'Asset', required=True)
    image = fields.Binary(string='Image')


class Menu(models.Model):
    _name = 'builder.website.menu'

    _order = 'sequence, id'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    sequence = fields.Integer('Sequence', default=60)
    name = fields.Char(string='Name', required=True)
    url = fields.Char("URL")
    page_id = fields.Many2one('builder.website.page', 'Page', required=True)
    parent_id = fields.Many2one('builder.website.menu', 'Parent')

    @api.onchange('page_id')
    def onchange_page_id(self):
        if not self.name and self.page_id:
            self.name = self.page_id.attr_name
            self.url = '/page/website.' + self.page_id.attr_id

SNIPPET_TEMPLATE = Template("""<data name="{{ object.name }}" inherit_id="website.snippets">
    <xpath expr="//div[@id='snippet_{{ object.category if not object.is_custom_category else 'effect' }}']" position="inside">
        <div>
            <div class="oe_snippet_thumbnail">
                <span class="oe_snippet_thumbnail_img" src="data:base64,{{ object.image }}"/>
                <span class="oe_snippet_thumbnail_title">{{ object.name }}</span>
            </div>
            <div class="oe_snippet_body {{ object.snippet_id }}">
                {{ object.content }}
            </div>
        </div>
    </xpath>
    <xpath expr="//div[@id='snippet_options']" position="inside">
        <div data-snippet-option-id='{{ object.snippet_id }}'
             data-selector=".{{ object.snippet_id }}"
             data-selector-siblings="{{ object.siblings|default('') }}"
             data-selector-children="{{ object.children|default('') }}"
             >
        </div>
    </xpath>
</data>
""")


class WebsiteSnippet(models.Model):
    _name = 'builder.website.snippet'
    _inherit = ['ir.mixin.orm.onchange.bugfix']

    _inherits = {
        'ir.ui.view': 'view_id'
    }

    # name is a field of the view
    # name = fields.Char('Name', required=True)

    # in the view this field is priority
    # sequence = fields.Integer('Sequence')

    category = fields.Selection(
        selection=[
            ('structure', 'Structure'),
            ('content', 'Content'),
            ('feature', 'Features'),
            ('effect', 'Effects'),
            ('custom', 'Custom'),
        ],
        string='Category',
        required=True
    )

    is_custom_category = fields.Boolean('Is Custom Category', compute='_compute_is_custom_category')

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade', required=True)
    view_id = fields.Many2one('ir.ui.view', 'View', ondelete='restrict', required=True)

    # Source
    source_url = fields.Char('Source URL', readonly=True)
    xpath = fields.Char('XPath', readonly=True)

    # Snippet
    snippet_id = fields.Char('ID', compute='_compute_snippet_id', store=True, readonly=False, required=True)
    # can't be Html because sanitize the images src
    content = fields.Text('Content', required=True)
    image = fields.Binary('Image')

    # Options
    siblings = fields.Char('Allowed Siblings')
    children = fields.Char('Allowed Children')

    @api.model
    def _default_inherit_id(self):
        return self.env.ref('website.snippets')

    _defaults = {
        'category': 'custom',
        'priority': 0,
        'type': 'qweb',
        'mode': 'extension',
        'inherit_id': _default_inherit_id
    }

    @api.one
    @api.depends('name')
    def _compute_snippet_id(self):
        self.snippet_id = self.name.lower().replace(' ', '_').replace('.', '_') if self.name else False

    @api.one
    @api.depends('category')
    def _compute_is_custom_category(self):
        self.is_custom_category = self.category == 'custom'

    @api.onchange('content', 'name', 'image', 'snippet_id', 'category', 'siblings', 'children')
    def compute_arch(self):
        # bug: arch field has a limit in the string size
        self.arch = SNIPPET_TEMPLATE.render(object=self)

    @api.onchange('snippet_id')
    def compute_xml_id(self):
        self.xml_id = self.snippet_id


class Module(models.Model):
    _inherit = 'builder.ir.module.module'

    website_menu_ids = fields.One2many('builder.website.menu', 'module_id', 'Menu')
    website_asset_ids = fields.One2many('builder.website.asset', 'module_id', 'Assets')
    website_theme_ids = fields.One2many('builder.website.theme', 'module_id', 'Themes')
    website_page_ids = fields.One2many('builder.website.page', 'module_id', 'Pages')
    website_snippet_ids = fields.One2many('builder.website.snippet', 'module_id', 'Snippets')





