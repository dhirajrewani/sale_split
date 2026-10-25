import { Component, t, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/** Popover content: explains the limit and offers the split button. */
export class QtySplitPopover extends Component {
    static template = "sale_qty_split.QtySplitPopover";
    props = useProps({
        record: t.object(),
        close: t.function().optional(),
    });

    setup() {
        this.orm = this.env.services.orm;
        this.action = this.env.services.action;
    }

    get data() {
        return this.props.record.data;
    }

    get productName() {
        const p = this.data.product_id;
        return (Array.isArray(p) ? p[1] : p && p.display_name) || "";
    }

    async onSplit() {
        const order = this.props.record.model.root;
        const records = order.data.order_line.records;
        const index = records.indexOf(this.props.record);
        const saved = await order.save();
        if (saved === false || !order.resId) {
            return;
        }
        const line = index >= 0 ? order.data.order_line.records[index] : this.props.record;
        if (!line || !line.resId) {
            return;
        }
        const action = await this.orm.call(
            "sale.order",
            "action_split_over_limit",
            [[order.resId]],
            { line_ids: [line.resId] }
        );
        this.action.doAction(action);
    }
}

/** Warning icon shown in the order line list when the qty exceeds the limit. */
export class QtySplitWidget extends Component {
    static template = "sale_qty_split.QtySplitWidget";
    props = useProps(standardFieldProps);

    setup() {
        this.popover = usePopover(QtySplitPopover, { position: "top" });
    }

    get isOver() {
        return (this.props.record.data[this.props.name] || 0) > 0;
    }

    showPopup(ev) {
        this.popover.open(ev.currentTarget, { record: this.props.record });
    }
}

registry.category("fields").add("qty_split_widget", {
    component: QtySplitWidget,
    supportedTypes: ["float"],
});
