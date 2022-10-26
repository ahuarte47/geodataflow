(function (window) {
  window["env"] = window["env"] || {};

  // Environment variables
  window["env"]["outputsPath"] = "${GEODATAFLOW_WORKBENCH_OUTPUT_PATH_PREFIX}";
  window["env"]["dataFolder"] = "${GEODATAFLOW_OUTPUT_FOLDER_PREFIX}";
  window["env"]["apiUrl"] = "${GEODATAFLOW_API_URL}";

  console.log("INFO: Workbench Settings:");
  console.log("INFO: + GeodataFlow API URL: " + window["env"]["apiUrl"]);
  console.log("INFO: + Outputs Path: " + window["env"]["outputsPath"]);

})(this);
