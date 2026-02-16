from odoo.tests.common import TransactionCase

class TestPriceCalculatorEncimera(TransactionCase):

    def setUp(self):
        super(TestPriceCalculatorEncimera, self).setUp()
        self.TemplateItem = self.env['vgr.price.template.item.worktop']
        self.Wizard = self.env['vgr.price.calculator.encimera.wizard']
        
        # Create a product for testing
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })

        # Create templates
        self.template_normal = self.TemplateItem.create({
            'name': 'Normal Template',
            'length': 0.0,
            'width': 0.0,
            'skip_price_calculation': False,
        })

        self.template_skip = self.TemplateItem.create({
            'name': 'Skip Template',
            'length': 0.0,
            'width': 0.0,
            'skip_price_calculation': True,
        })

    def test_price_calculation_skip(self):
        """Test that skip_price_calculation prevents unit_price update"""
        # Create wizard
        wizard = self.Wizard.create({
            'product_id': self.product.id,
            'precio_ml': 100.0,
            'grosor': 12.0,
        })

        # Manually trigger creating default templates (simulating default_get behavior)
        # In a real test we might just create lines directly attached to wizard
        
        # Check that templates were created
        # We need to simulate how templates are added. 
        # The wizard's default_get does it, but here we just created the wizard record.
        # Let's create lines manually to test the compute/onchange logic specifically.

        line_normal = self.env['vgr.price.calculator.encimera.template'].create({
            'calculator_id': wizard.id,
            'template_id': self.template_normal.id,
            'name': self.template_normal.name,
            'ml_measurement': 2.0,
            'unit_price': 0.0,
            'skip_price_calculation': self.template_normal.skip_price_calculation,
        })

        line_skip = self.env['vgr.price.calculator.encimera.template'].create({
            'calculator_id': wizard.id,
            'template_id': self.template_skip.id,
            'name': self.template_skip.name,
            'ml_measurement': 2.0,
            'unit_price': 50.0, # Pre-set value
            'skip_price_calculation': self.template_skip.skip_price_calculation,
        })

        # Test Compute Logic (if it depends on calculator_id.precio_ml)
        # The compute method `_compute_unit_price` depends on `calculator_id.precio_ml`.
        
        # Trigger recomputation if needed
        line_normal._compute_unit_price()
        line_skip._compute_unit_price()

        # Check normal line
        # ml_measurement=2.0, precio_ml=100.0 -> unit_price should be 200.0
        self.assertEqual(line_normal.unit_price, 200.0, "Normal line should calculate price")

        # Check skip line
        # It should NOT have changed from 50.0 to 200.0
        self.assertEqual(line_skip.unit_price, 50.0, "Skip line should NOT calculate price")

    def test_onchange_logic(self):
        """Test onchange logic in wizard"""
        wizard = self.Wizard.create({
            'product_id': self.product.id,
            'precio_ml': 100.0,
        })
        
        # Create templates using the wizard's relation
        # We need to use new() for onchange tests ideally, but let's test the method directly
        
        line_normal = self.env['vgr.price.calculator.encimera.template'].create({
            'calculator_id': wizard.id,
            'ml_measurement': 2.0,
            'skip_price_calculation': False,
        })
        
        line_skip = self.env['vgr.price.calculator.encimera.template'].create({
            'calculator_id': wizard.id,
            'ml_measurement': 2.0,
            'unit_price': 50.0,
            'skip_price_calculation': True,
        })
        
        # Change price on wizard
        wizard.precio_ml = 200.0
        
        # call onchange manually
        wizard._onchange_precio_ml_templates()
        
        # Check normal line
        self.assertEqual(line_normal.unit_price, 400.0, "Normal line should update on onchange")
        
        # Check skip line
        self.assertEqual(line_skip.unit_price, 50.0, "Skip line should NOT update on onchange")
