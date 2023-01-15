/*
  ===============================================================================

   GeodataFlow:
   Geoprocessing framework for geographical & Earth Observation (EO) data.

   Copyright (c) 2022-2023, Alvaro Huarte. All rights reserved.

   Redistribution and use of this code in source and binary forms, with
   or without modification, are permitted provided that the following
   conditions are met:
   * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.

   THIS CODE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
   TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
   OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SAMPLE CODE, EVEN IF
   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

  ===============================================================================
*/

// Utility functions to provide HTML content to the Application.
class HtmlContent {

  // Gets or creates a TreeNode for the specified path.
  static getCategoryNode(parentNode, pathOfNode) {
    if (pathOfNode) {
      const parts = pathOfNode.split('/');
      let nodeId = 'category';

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        nodeId += '-' + part;

        var nodeDiv = document.getElementById(nodeId);
        if (nodeDiv == undefined) {
          let html = `
            <li>
              <div class="category-box">
                <span class="category" onmouseover="mouseOverNode(event)" id="${nodeId}">${part}</span>
                <ul class="category-nested" id="${nodeId}_nested">
                </ul>
              </div>
            </li>`;

          nodeDiv = document.createElement('div');
          nodeDiv.innerHTML = html;
          parentNode.appendChild(nodeDiv);
        }
        parentNode = document.getElementById(nodeId + '_nested');
      }
    }
    return parentNode;
  }

  // Returns the HTML content of the specified parameter of a Module.
  static getHtmlContentOfParameter(paramName, param, data) {
    var html = '';
    let dataTypes = Array.isArray(param.dataType) ? param.dataType : param.dataType.toString().split(',');
    let defaultValue = param.default !== undefined ? param.default : '';

    // Inject HTML content of each available DataType (It can be more than one).
    for (let i = 0; i < dataTypes.length; i++) {
      let dataType = dataTypes[i].toLowerCase();
      let isHidden = dataTypes.length > 1 && i > 0 ? 'hidden' : '';
      let key = paramName.toLowerCase();
      if (dataTypes.length > 1) { key = dataType + '_for_' + key; }

      // ... is there defined a list of options?
      if (param.options) {
        let labels = param.labels ? param.labels : param.options;
        html += `<select class="parameter-select" df-${key} ${isHidden}>`;
        data[key] = defaultValue;

        for (let j = 0; j < param.options.length; j++) {
          let optionValue = param.options[j];
          let optionLabel = labels[j];
          let isSelected = optionValue == defaultValue ? 'selected' : ''
          html += `<option value="${optionValue}" ${isSelected}>${optionLabel}</option>`;
        }
        html += '</select>';
      }
      // ... otherwise injecting HTML content according to current DataType.
      else {
        switch (dataType) {
          case 'integer':
          case 'int':
          case 'long': {
            html += `<input type="text" class="parameter-text" oninput="this.value = stringAsInteger(this.value);" value="${defaultValue}" df-${key} ${isHidden}>`;
            data[key] = defaultValue;
            break;
          }
          case 'float':
          case 'double': {
            html += `<input type="number" class="parameter-text" step="any" value="${defaultValue}" df-${key} ${isHidden}>`;
            data[key] = defaultValue;
            break;
          }
          case 'date': {
            html += `<input type="text" class="parameter-datepicker" placeholder="YYYY-MM-DD" value="${defaultValue}" df-${key} ${isHidden}>`;
            data[key] = defaultValue;
            break;
          }
          case 'url': {
            html += `<input type="url" class="parameter-text" placeholder="https://example.com" value="${defaultValue}" df-${key} ${isHidden}>`;
            data[key] = defaultValue;
            break;
          }
          case 'boolean':
          case 'bool': {
            let boolValue = defaultValue.toString().toLowerCase() == 'true' ? 'checked' : '';
            let labelText = param.description ? param.description.replaceAll('"', "'") : '';
            data[key] = defaultValue;

            html += `
              <table style="width:100%" ${isHidden}>
                <tr>
                  <td><input type="checkbox" class="parameter-boolean" onclick="_parameterLabelBool_onClick(event, false)" ${boolValue}></td>
                  <td><label onclick="_parameterLabelBool_onClick(event, true)">${labelText}</label></td>
                  <td><input type="text" style="display:none;" onchange="_parameterLabelBool_onChange(event)" value="${defaultValue}" data-key="${key}"></td>
                </tr>
              </table>`;

            break;
          }
          case 'geojson': {
            html += `
              <div style="overflow:clip;white-space:nowrap;" ${isHidden}>
                <input type="button" class="parameter-button" onclick="_drawGeometry_onClick(event)" value="Draw geometry..." data-key="${key}">
                <span style="padding-left:4px;"></span>
              </div>`;

            break;
          }
          case 'file': {
            let fileExtensions = param.extensions ? param.extensions.join(', ') : '';
            html += `
              <div style="overflow:clip;white-space:nowrap;" ${isHidden}>
                <input type="button" class="parameter-button" onclick="_uploadFile_onClick(event)" value="Select file..." data-key="${key}" data-extensions="${fileExtensions}">
                <span style="padding-left:4px;"></span>
              </div>`;

            break;
          }
          case 'calc':
            // TODO: Implement one Expression Builder UI component.
          case 'filter':
            // TODO: Implement one Query Builder UI component.
          case 'crs':
            // TODO: Implement one EPSG Selector UI component.
          default: {
            let placeHolder = param.placeHolder || '';
            html += `<input type="text" class="parameter-text" placeholder="${placeHolder}" value="${defaultValue}" df-${key} ${isHidden}>`;
            data[key] = defaultValue;
            break;
          }
        }
      }
    }

    // There are more than one options of DataTypes, allowing to choose between one of them.
    if (dataTypes.length > 1) {
      let key = paramName.toLowerCase();
      let options = '';
      data[key] = `$(${dataTypes[0]}_for_${key})`;

      for (let i = 0; i < dataTypes.length; i++) {
        let isSelected = (i === 0) ? 'selected' : '';
        options += `<option value="$(${dataTypes[i]}_for_${key})" ${isSelected}>${dataTypes[i]}</option>`;
      }
      html = `
        <table style="width:100%;">
          <tr>
            <td style="width:85px;">
              <select class="parameter-select" onchange="_parameterDataTypes_onChange(event)" df-${key}>${options}</select>
            </td>
            <td>${html}</td>
          </tr>
        </table>`;
    }
    return html;
  }

  // Returns the HTML content of the specified Module.
  static getHtmlContentOfModule(moduleType, module, nodeData) {
    let moduleDiv = document.createElement('div');
    let params = module['params'];

    if (params) {
      Object.entries(params).forEach(([key, param]) => {
        let description = param.description ? param.description.replaceAll('"', "'") : '';
        let html = '<div class="parameter-row">';

        if (param.dataType == 'input') {
          html += `
            <i class="parameter-icon fas fa-arrow-right"></i>
            <div class="parameter-label parameter-noeditable" onmouseover="mouseOverNode(event)" toolTip="${description}"> ${key}
            </div>`;
        }
        else {
          html += `
            <i class="parameter-icon far fa-circle"></i>
            <div class="parameter-label" onclick="editParameterOfModule(event)" onmouseover="mouseOverNode(event)" toolTip="${description}" data-type="${moduleType}" data-module="${module.name}" data-param="${key}"> ${key}
              <div class="modal-node" style="display:none">
                <div class="modal-content">
                  <div class="title-box" onclick="finishEditionOfParameter(event)" onmouseover="mouseOverNode(event)" toolTip="${description}">
                    <i class="parameter-icon fas fa-circle"></i> ${key}
                    <span class="close" onclick="closeModal(event)">&times;</span>
                  </div>
                  <div class="parameter-box">
                    ${HtmlContent.getHtmlContentOfParameter(key, param, nodeData)}
                  </div>
                </div>
              </div>
            </div>`;
        }
        html += '</div>'

        let parameterDiv = document.createElement('div');
        parameterDiv.innerHTML = html;
        moduleDiv.appendChild(parameterDiv);
      });
    }
    return moduleDiv.innerHTML;
  }

  // Returns the HTML content of the specified Requests Report Table.
  static getHtmlContentOfRequestsTable(reports, dataFolder = undefined, outputsPath = undefined) {
    let html = `
      <table class="requestsTable">
        <thead>
          <tr>
            <th>Workflow ID</th>
            <th>Status</th>
            <th>Created</th>
            <th>Elapsed time</th>
            <th>Info</th>
          </tr>
        </thead>
        <tbody>`;

    Object.values(reports).sort(sortReports).forEach(function(report) {
      let workflowId = report['workflow_id'];
      let status = report['status'];
      let createdAtTime = report['created_at'] ? report['created_at'].substring(0,19).replaceAll('T', ' ') : '';
      let elapsedTime = '';
      let info = report['message'] || '';

      // Calculate elapsed Time.
      if (report['created_at'] && report['terminated_at']) {
        const date1 = new Date(report['created_at']);
        const date2 = new Date(report['terminated_at']);
        const date3 = new Date(date2.getTime() - date1.getTime());
        elapsedTime = date3.toISOString().substring(11,23);
      }
      // Link to ZIP with outputs.
      if (status == 'OK' && report['file_result']) {
        let output_href = report['file_result'];
        if (dataFolder && outputsPath) {
          output_href = output_href.replaceAll(dataFolder, outputsPath);
        }
        info = `<a href="${output_href}" target="_blank" title="Link to file with Results">Output</a>`;
      }

      html += `
        <tr>
          <td>${workflowId}</td>
          <td class="${status=='OK' ? 'td_ok' : (status=='ERROR' ? 'td_error': 'td_working')}">${status}</td>
          <td>${createdAtTime}</td>
          <td>${elapsedTime}</td>
          <td>${info}</td>
        </tr>`;
    });
    return html + '</tbody></table>';
  }
}

// ============================================================================
// UI utility functions
// ============================================================================

// The user selects a DataType of a Parameter from a list of available ones.
function _parameterDataTypes_onChange(event) {
  let selectDiv = event.target;
  let tableDiv = selectDiv.closest('table');
  let tdsDiv = tableDiv.querySelectorAll('td');

  for (let i = 0; i < selectDiv.children.length; i++) {
    let tempDiv = tdsDiv[1].children[i];
    tempDiv.style.display = (selectDiv.selectedIndex === i) ? 'block' : 'none';
  }
}

// The user changes the value of a bool-type parameter.
function _parameterLabelBool_onClick(event, flipCheckBox) {
  let labelDiv = event.target;

  let tableDiv = labelDiv.closest('table');
  let checkDiv = tableDiv.querySelector('input[type=checkbox]');
  let inputDiv = tableDiv.querySelector('input[type=text]');

  // ... to correctly update the DOM.
  if (flipCheckBox) {
    if (checkDiv.checked) { checkDiv.removeAttribute('checked'); } else { checkDiv.setAttribute('checked', null); }
  }
  else {
    if (checkDiv.checked) { checkDiv.setAttribute('checked', null); } else { checkDiv.removeAttribute('checked'); }
  }
  inputDiv.setAttribute('value', checkDiv.checked ? 'true' : 'false');

  let dataKey = inputDiv.getAttribute('data-key');
  let nodeId = inputDiv.closest('.drawflow-node').getAttribute('id').slice(5);
  let nodeConfig = editor.getNodeConfig(nodeId);
  nodeConfig.data[dataKey] = (inputDiv.value != 'false');
}
function _parameterLabelBool_onChange(event) {
  let labelDiv = event.target;

  let tableDiv = labelDiv.closest('table');
  let checkDiv = tableDiv.querySelector('input[type=checkbox]');
  let inputDiv = tableDiv.querySelector('input[type=text]');

  // ... to correctly update the DOM.
  if (inputDiv.value != 'false') {
    checkDiv.setAttribute('checked', null);
  }
  else {
    checkDiv.removeAttribute('checked');
  }
  inputDiv.setAttribute('value', checkDiv.checked ? 'true' : 'false');

  let dataKey = inputDiv.getAttribute('data-key');
  let nodeId = inputDiv.closest('.drawflow-node').getAttribute('id').slice(5);
  let nodeConfig = editor.getNodeConfig(nodeId);
  nodeConfig.data[dataKey] = (inputDiv.value != 'false');
}

// The user wants to upload a file to use as input.
function _uploadFile_onClick(event) {
  let button = event.target;

  // Getting user settings.
  let dataKey = button.getAttribute('data-key');
  let nodeId = button.closest('.drawflow-node').getAttribute('id').slice(5);
  let nodeConfig = editor.getNodeConfig(nodeId);

  let fileRef = nodeConfig.data[dataKey];
  let fileExtensions = button.getAttribute('data-extensions');
  let acceptAttr = fileExtensions ? 'accept="' + fileExtensions + '"' : '';

  // Start new UI for selecting a File.
  let workbenchDiv = document.querySelector('.workbench');
  let dialogDiv = document.querySelector('.dialog');
  let contentDiv = dialogDiv.querySelector('.dialog-content');
  contentDiv.innerHTML = '';

  let uploadDiv = document.createElement('div');
  uploadDiv.setAttribute('id', 'parameter-upload');
  contentDiv.appendChild(uploadDiv);
  workbenchDiv.style.display = 'none';
  dialogDiv.style.display = 'block';

  // Create the Upload file box.
  let html = `
    <div class="modal-window-area">
      <div class="icon"><i class="fas fa-cloud-upload-alt"></i></div>
      <span class="label">Drag & Drop to Upload File</span>
      <span>OR</span>
      <button>Browse File</button>
      <input type="file" ${acceptAttr} hidden>
      <div class="upload-file-area" hidden>
        <p></p>
      </div>
      <div class="upload-file-area" hidden>
        <div class="icon"><i class="fas fa-file-alt"></i></div>
        <span class="data"></span>
        <span class="close" title="Remove File">&times;</span>
      </div>
    </div>`;
  uploadDiv.innerHTML = html;

  let dropArea = document.querySelector('.modal-window-area');
  let dragText = dropArea.querySelector('.label');
  let fileButton = dropArea.querySelector('button');
  let fileInput = dropArea.querySelector('input');
  let removeButton = dropArea.querySelector('.close');
  var dragCounter = 0;

  // Events!

  dropArea.addEventListener('dragenter', (event)=>{
    dragCounter++;
  });
  dropArea.addEventListener('dragover', (event)=>{
    event.preventDefault();
    dropArea.classList.add('active');
    dragText.textContent = 'Release to Upload File';
  });
  dropArea.addEventListener('dragleave', ()=>{
    event.preventDefault();
    dragCounter--;

    if (dragCounter === 0) {
      dropArea.classList.remove('active');
      dragText.textContent = 'Drag & Drop to Upload File';
    }
  });
  dropArea.addEventListener('drop', (event)=>{
    event.preventDefault();
    fileRef = event.dataTransfer.files[0];
    dropFile(fileRef, true);
  });
  fileButton.onclick = ()=>{
    fileInput.click(); // If user click on the button then the input also clicked.
  };
  fileInput.addEventListener('change', function() {
    fileRef = this.files[0];
    dropFile(fileRef, true);
  });
  removeButton.onclick = ()=>{
    dropFile(null, true);
  }

  // Doing things when the user closes the Dialog.
  function _finishCallback(callbackArgs) {
    //...
  }
  contentDiv.finishCallbackArgs = [];
  contentDiv.finishCallback = _finishCallback;

  // The user selected a new File!
  function dropFile(fileRef, dataChanged = false) {
    dragCounter = 0;
    dropArea.classList.remove('active');
    dragText.textContent = 'Drag & Drop to Upload File';

    // Fill metadata info of selected file.
    if (fileRef) {
      let fileName = fileRef.name;
      if (fileName.lastIndexOf('.') == -1) { return; } // Ignore, maybe a folder!

      let fileSize = fileRef.size;
      if (fileName.length >= 20) {
        const lastIndex = fileName.lastIndexOf('.');
        const fileExt = fileName.substring(lastIndex);
        fileName = fileName.substring(0, 20-fileExt.length) + "..." + fileExt;
      }
      let fileInfo = `${fileName} [${formatBytes(fileSize)}]`;
      dropArea.querySelector('.data').textContent = fileInfo;

      button.parentNode.querySelector('span').textContent = ' ' + fileInfo;
      dropArea.querySelectorAll('.upload-file-area').forEach(function(element) { element.style.display = 'flex'; });

      // ... save custom data of current Node.
      if (dataChanged) {
        dataRef = {
          'lastModified': fileRef.lastModified,
          'lastModifiedDate': fileRef.lastModifiedDate,
          'name': fileRef.name,
          'size': fileRef.size,
          'type': fileRef.type
        };

        const fileReader = new FileReader();
        fileReader.onload = function() {
          let fileData = fileReader.result;
          dataRef['fileData'] = fileData;
        }
        fileReader.readAsDataURL(fileRef);

        nodeConfig.data[dataKey] = dataRef;
      }
    }
    else {
      button.parentNode.querySelector('span').textContent = '';
      dropArea.querySelectorAll('.upload-file-area').forEach(function(element) { element.style.display = 'none'; });

      // ... save custom data of current Node.
      if (dataChanged) {
        nodeConfig.data[dataKey] = undefined;
      }
    }
  }
  dropFile(fileRef, false);
}

// The user wants to draw a Geometry (GeoJson) to use as input.
function _drawGeometry_onClick(event) {
  let button = event.target;

  // Getting user settings.
  let dataKey = button.getAttribute('data-key');
  let nodeId = button.closest('.drawflow-node').getAttribute('id').slice(5);
  let nodeConfig = editor.getNodeConfig(nodeId);
  let featureCollection = nodeConfig.data[dataKey];
  let features = featureCollection !== undefined ? featureCollection.features : [];

  // Start new UI for drawing geometries.
  let workbenchDiv = document.querySelector('.workbench');
  let dialogDiv = document.querySelector('.dialog');
  let contentDiv = dialogDiv.querySelector('.dialog-content');
  contentDiv.innerHTML = '';

  let mapDiv = document.createElement('div');
  mapDiv.setAttribute('id', 'parameter-map');
  contentDiv.appendChild(mapDiv);
  workbenchDiv.style.display = 'none';
  dialogDiv.style.display = 'block';

  // Create the Leaflet map.
  let map = L.map('parameter-map', {});
  let osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { noWrap: true });
  osmLayer.addTo(map);
  let geocoder = L.Control.geocoder({position: 'topleft'});
  geocoder.addTo(map);
  let mousePos = L.control.mousePosition({position: 'bottomleft', emptyString: '', prefix: '<b>LatLng:</b> ', numDigits: 5});
  mousePos.addTo(map);
  let scaleBar = L.control.scale({position: 'bottomright'});
  scaleBar.addTo(map);

  // Layer Control with two Basemaps.
  let satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { noWrap: true });
  let baseLayers = {'OSM Standard': osmLayer, 'ESRI Satellite': satLayer};
  let layerControl = L.control.layers(baseLayers, {}, {position: 'topright'});
  layerControl.addTo(map);

  // Append Draw control.
  let editableLayers = new L.FeatureGroup();
  features.forEach((feature) => { L.geoJson(feature).getLayers().forEach((layer) => { editableLayers.addLayer(layer); }); });
  //
  map.addLayer(editableLayers);
  let drawOptions = {
    position: 'topleft',
    draw: {
      circle: false,
      marker: false,
      circlemarker: false,
      polyline: false,
      polygon: { repeatMode: true, allowIntersection: false },
      rectangle: { repeatMode: true, shapeOptions: { clickable: true } }
    },
    edit: {
      featureGroup: editableLayers,
      remove: true
    }
  };
  map.on(L.Draw.Event.CREATED, function (event) {
    editableLayers.addLayer(event.layer);
  });
  let drawControl = new L.Control.Draw(drawOptions);
  map.addControl(drawControl);

  // Append FileLoader control.
  L.Control.FileLayerLoad.LABEL = '<i class="fas fa-folder-open fa-xs" style="text-align:center;vertical-align:middle;"></i>';
  fileLoaderControl = L.Control.fileLayerLoad({
    fitBounds: true,
    addToMap: false
  });
  fileLoaderControl.addTo(map);
  fileLoaderControl.loader.on('data:loaded', function (event) {
    event.layer.getLayers().forEach((layer) => { editableLayers.addLayer(layer); });
  });

  // Doing things when the user closes the Dialog.
  function _finishCallback(callbackArgs) {
    let featureCollection = editableLayers.toGeoJSON();
    let features = featureCollection.features;
    nodeConfig.data[dataKey] = featureCollection;
    button.parentNode.querySelector('span').textContent = (features.length === 0) ? '' : (features.length + ' geometries');
  }
  contentDiv.finishCallbackArgs = [];
  contentDiv.finishCallback = _finishCallback;

  // Fit map.
  if (editableLayers.getLayers().length > 0) {
    map.fitBounds(editableLayers.getBounds());
  }
  else {
    map.setView([10, 0], 2);
  }
}

// Sorts reports by INV date.
function sortReports(a, b) {
  let startTimeA = a["created_at"];
  let startTimeB = b["created_at"];
  return startTimeB.localeCompare(startTimeA);
}
