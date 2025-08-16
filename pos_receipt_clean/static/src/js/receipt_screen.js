/** @odoo-module **/

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";

patch(ReceiptScreen.prototype, {
    async downloadReceipt() {
        try {
            // Generate the receipt image
            const receiptImage = await this.generateTicketImage();
            
            // Create a download link
            const link = document.createElement('a');
            link.href = receiptImage;
            
            // Set filename with order name and timestamp
            const order = this.currentOrder;
            const orderName = order.name || 'receipt';
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:\-T]/g, '');
            link.download = `${orderName}_${timestamp}.jpg`;
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success notification if available
            if (this.notification) {
                this.notification.add('Receipt downloaded successfully!', { type: 'success' });
            }
        } catch (error) {
            console.error('Error downloading receipt:', error);
            // Show error notification if available
            if (this.notification) {
                this.notification.add('Failed to download receipt. Please try again.', { type: 'danger' });
            }
        }
    }
});
