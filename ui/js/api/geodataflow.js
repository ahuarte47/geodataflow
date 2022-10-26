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

// Implements a Workflow engine using the GeodataFlow tolkit.
class GeodataFlow {

  // Constructor of Class.
  constructor(apiUrl) {
    this.apiUrl = apiUrl;
  }

  // Returns the name of this Workflow engine.
  name() {
    return 'GeodataFlow';
  }

  // Returns the collection of Modules supported by this Workflow engine.
  async modules() {
    if (this.apiUrl) {
      const response = await fetch(this.apiUrl + '/modules', {
        method: 'GET',
        headers: new Headers({'Content-Type': 'application/json; charset=utf-8'}),
        mode: 'cors'
      });
      const result = await response.json();
      return result;
    }
    // ... fake API to demos.
    else {
      const script = document.createElement('script');
      script.type = 'text/javascript';
      script.src = 'js/api/modules.js';
      document.body.appendChild(script);
      await new Promise((resolve) => script.onload = resolve);
      return modules;
    }
  }

  // Returns the list of Workflows requested by an User.
  async workflows(user_id) {
    if (this.apiUrl) {
      const response = await fetch(this.apiUrl + '/workflows?user_id='+user_id, {
        method: 'GET',
        headers: new Headers({'Content-Type': 'application/json; charset=utf-8'}),
        mode: 'cors'
      });
      const result = await response.json();
      return result;
    }
    // ... fake API to demos.
    else {
      throw Error('There is none WebAPI URL configured, you are using a fake client for demo purposes.');
    }
  }

  // Run the specified Geodataflow pipeline.
  async run(user_id, pipeline, pipelineArgs = undefined) {
    if (this.apiUrl) {
      const payload = {'user_id': user_id, 'input': {'pipeline': pipeline}};
      if (pipelineArgs !== undefined) { payload['input_args'] = pipelineArgs };

      const response = await fetch(this.apiUrl + '/workflows', {
        method: 'POST',
        headers: new Headers({'Content-Type': 'application/json; charset=utf-8'}),
        mode: 'cors',
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      return result;
    }
    else {
      throw Error('There is none WebAPI URL configured, you are using a fake client for demo purposes.');
    }
  }

  // Get the Schema of a Stage in the specified Geodataflow pipeline.
  async getSchema(user_id, pipeline, stageId) {
    if (this.apiUrl) {
      const payload = {'user_id': user_id, 'input': {'pipeline': pipeline}};

      const response = await fetch(this.apiUrl + '/schema?stageId='+stageId, {
        method: 'POST',
        headers: new Headers({'Content-Type': 'application/json; charset=utf-8'}),
        mode: 'cors',
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      return result;
    }
    else {
      throw Error('There is none WebAPI URL configured, you are using a fake client for demo purposes.');
    }
  }
};
