var morsels = window.morsels || {};

morsels.start = {
    init: function() {
        "use strict";
        if ($("#fileupload").size()) {
	        morsels.fileUpload.init();
        }
    }
};

morsels.start.init();