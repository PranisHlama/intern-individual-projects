// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {Attachment} from "@mail/core/common/attachment_model";
import {patch} from "@web/core/utils/patch";

const dmsContentUrl = (id) =>
    `/web/content?id=${id}&field=content&model=dms.file&filename_field=name`;

// Only dms.file records get custom URLs; regular attachments keep core behaviour.
patch(Attachment.prototype, {
    get defaultSource() {
        if (this.model_name !== "dms.file") {
            return super.defaultSource;
        }
        if (this.isImage) {
            return `${dmsContentUrl(this.id)}&download=false`;
        }
        return dmsContentUrl(this.id);
    },
    get downloadUrl() {
        if (this.model_name !== "dms.file") {
            return super.downloadUrl;
        }
        return `${dmsContentUrl(this.id)}&download=true`;
    },
});
