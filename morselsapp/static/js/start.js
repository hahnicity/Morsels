/*global $, _ */
var morsels = window.morsels || {};

(function () {
	"use strict";

	morsels.start = {
		init: function () {
			if ($("#fileupload").size()) {
				morsels.fileUpload.init();
			}
		}
	};

	morsels.start.init();

}());