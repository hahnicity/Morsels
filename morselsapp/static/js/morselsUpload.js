/*global $, _ */
var morsels = window.morsels || {};

(function () {
	"use strict";
	var init, addUploadUI;

	init = function () {
		addUploadUI();
	};

	addUploadUI = function (options) {
		var uploadWidget = $('#fileupload');

		uploadWidget.fileupload({
			acceptFileTypes: /(\.|\/)(jpe?g)|png|ogg|gif|tiff|bmp|ico|mp3$/i, //Add supported file types here
			maxNumberOfFiles: 10, //Change max number of files
			maxChunkSize: 512 * 1024, //500KB each request will send 500KB of data.
			maxRetries: 20, //Number of times to retry upload
			retryTimeout: 1000,
			sequentialUploads: true,
			autoUpload: false,
			multipart: true,

			uploadTemplateId: $("#template-upload").html(),
			downloadTemplateId: $("#template-download").html(),

			add: function (e, data) {
				//Hook for adding a new file to the uploader
				var self = this,
					fileName = data.files[0].name;

				$.getJSON(uploadWidget.fileupload('option', 'url'), {file: fileName}, function (response) {
					data.url = response && response.url;
					data.uploadedBytes = response && response.size;
					$.blueimp.fileupload.prototype.options.add.call(self, e, data);
					uploadWidget.addClass('ready');
				});
			},

			fail: function (e, data) {
				var self = this,
					fileName = data.files[0].name,
					fu = $(self).data('fileupload'),
					retries = data.context.data('retries') || 0,
					retry = function () {
						$.getJSON(morsels.urls.IMAGE_UPLOAD, {file: fileName})
							.done(function (response) {
								data.uploadedBytes = response && response.size;
								data.submit();
							})
							.fail(function () {
								fu._trigger('fail', e, data);
							});
					};

				if (data.errorThrown !== 'abort' && data.errorThrown !== 'uploadedBytes' && retries < fu.options.maxRetries) {
					retries += 1;
					data.context.data('retries', retries);
					window.setTimeout(retry, retries * fu.options.retryTimeout);
					return;
				}
				data.context.removeData('retries');
				$.blueimpUI.fileupload.prototype.options.fail.call(self, e, data);
			}
		});
	};

	// export public functions:
	morsels.fileUpload = {init: init};
}());
