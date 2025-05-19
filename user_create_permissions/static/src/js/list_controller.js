/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

// Guardar referencias a los métodos originales
const originalSetup = ListController.prototype.setup;
const originalCreateRecord = ListController.prototype.createRecord;

patch(ListController.prototype, {
    setup() {
        originalSetup.call(this, ...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
    },

    async createRecord() {
        // Verificar permisos según el modelo
        if (this.props.resModel === 'res.partner') {
            const permissions = await this.orm.call('res.users', 'search_read',
                [[['id', '=', this.env.services.user.userId]]],
                {fields: ['can_create_partners']}
            );

            if (permissions.length && !permissions[0].can_create_partners) {
                this.notification.add(
                    "No tienes permiso para crear clientes.",
                    { type: "danger" }
                );
                return;
            }
        }
        else if (this.props.resModel === 'product.template' || this.props.resModel === 'product.product') {
            const permissions = await this.orm.call('res.users', 'search_read',
                [[['id', '=', this.env.services.user.userId]]],
                {fields: ['can_create_products']}
            );

            if (permissions.length && !permissions[0].can_create_products) {
                this.notification.add(
                    "No tienes permiso para crear productos.",
                    { type: "danger" }
                );
                return;
            }
        }

        // Si tiene permisos, comportamiento estándar
        await originalCreateRecord.call(this, ...arguments);
    },
});
