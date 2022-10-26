/*
  ===============================================================================

   GeodataFlow:
   Toolkit to run workflows on Geospatial & Earth Observation (EO) data.

   Copyright (c) 2022, Alvaro Huarte. All rights reserved.

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

// Modal MessageBox utility.
class MessageBox {

  // Show MessageBox.
  static show(messageContent, messageIcon='INFO', buttons=['OK'], defaultButtton=undefined, callbackFunction=undefined) {
    let iconName = '';
    let iconStyle = '';
    let htmlButtons = '';
    messageIcon = messageIcon.toUpperCase();
    if (defaultButtton == undefined) defaultButtton = buttons[0];

    switch (messageIcon) {
      case 'WARNING':
        iconName = 'fa-exclamation-triangle';
        iconStyle = "color:orange";
        break;
      case 'ERROR':
        iconName = 'fa-exclamation-triangle';
        iconStyle = "color:#da0b0b";
        break;
      case 'INFO':
      default:
        iconName = 'fa-info-circle';
        break;
    }
    for (let i = 0; i < buttons.length; i++) {
      let buttonClass = buttons.length > 1 && buttons[i] === defaultButtton ? 'class="default-button"' : '';
      htmlButtons += `<button ${buttonClass} onclick="_messageButton_onClick(event);">${buttons[i]}</button>\n`;
    }

    // Start new UI for showing a MessageBox.
    let workbenchDiv = document.querySelector('.workbench');
    let dialogDiv = document.querySelector('.dialog');
    let contentDiv = dialogDiv.querySelector('.dialog-content');
    contentDiv.innerHTML = '';

    let boxDiv = document.createElement('div');
    boxDiv.setAttribute('id', 'parameter-wnd');
    contentDiv.appendChild(boxDiv);
    workbenchDiv.style.display = 'none';
    dialogDiv.style.display = 'block';

    let htmlContent = '';
    if (messageContent instanceof HTMLElement) {
      htmlContent = messageContent.innerHTML;
    }
    else {
      htmlContent = `<label>${messageContent}</label>`;
    }

    // Create the box.
    let html = `
      <div class="modal-window-area">
        <div class="icon"><i class="fas ${iconName}" style="${iconStyle}"></i></div>
        <div class="modal-window-col">
          ${htmlContent}
        </div>
        <p></p>
        <div class="modal-window-row">
          ${htmlButtons}
        </div>
      </div>`;
    boxDiv.innerHTML = html;

    // Doing things when the user closes the Dialog.
    contentDiv.finishCallbackArgs = "Close";
    contentDiv.finishCallback = callbackFunction;
  }
}

// The user wants to close last MessageBox.
function _messageButton_onClick(event) {
  let button = event.target;

  document.querySelector('.workbench').style.display = 'block';
  document.querySelector('.dialog').style.display = 'none';

  let contentDiv = document.querySelector('.dialog-content');
  if (contentDiv.finishCallback) contentDiv.finishCallback(button.innerHTML);
}
