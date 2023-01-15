(function (window) {
  window["env"] = window["env"] || {};

  // Environment variables
  window["env"]["outputsPath"] = null;
  window["env"]["dataFolder"] = null;
  window["env"]["apiUrl"] = null;

  console.log("INFO: Workbench Settings:");
  console.log("INFO: + GeodataFlow API URL: " + window["env"]["apiUrl"]);
  console.log("INFO: + Outputs Path: " + window["env"]["outputsPath"]);

})(this);
