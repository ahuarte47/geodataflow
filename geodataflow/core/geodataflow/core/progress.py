# -*- coding: utf-8 -*-
"""
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

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
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
"""

# TQDM Python module installed?, therefore we can define a Callback Function.
_TQDM_STATE_KEY_ = 0
_TQDM_STATE_REF_ = None


class ProgressProcessingStore(object):
    """
    Shows the progress of a Pipeline Job walking on a DataStore.
    """
    def __init__(self, processing_args=None):
        self.enabled = True

        # Available UI percentage progress?
        if processing_args:
            self.enabled = hasattr(processing_args, 'ui_mode') and \
                bool(getattr(processing_args, 'ui_mode', False))

        self._tqdm = ProgressProcessingStore.validate_tqdm_ref() if self.enabled else None
        self.enabled = self._tqdm is not None
        self._progress_bar = None

    @staticmethod
    def validate_tqdm_ref():
        """
        Check if TQDM module is installed.
        """
        global _TQDM_STATE_KEY_
        global _TQDM_STATE_REF_

        if _TQDM_STATE_KEY_ == 0:
            try:
                from tqdm import tqdm
                _TQDM_STATE_KEY_ = 1
                _TQDM_STATE_REF_ = tqdm
            except Exception:
                import logging
                logging.warning('TQDM module not installed. Maybe Progress UI capabilities be unavailable.')
                _TQDM_STATE_KEY_ = 2
                _TQDM_STATE_REF_ = None

        return _TQDM_STATE_REF_

    def initialized(self):
        """
        Returns whether the Progress UI was already initialized.
        """
        return self._progress_bar is not None

    def initialize(self, item_count: int) -> bool:
        """
        Initializes the Progress UI to the specified count.
        """
        if not self.enabled or item_count <= 0:
            self._progress_bar = None
            return False
        elif self._progress_bar is not None:
            self._progress_bar.reset(item_count)
            return True
        else:
            self._progress_bar = self._tqdm(range(item_count), ncols=80)
            return True

    def update(self) -> None:
        """
        Updates the percentage progress of current Job.
        """
        if self._progress_bar:
            self._progress_bar.update()

        pass
