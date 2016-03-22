/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  describe('Launch Instance Configuration Step', function() {

    describe('LaunchInstanceConfigurationCtrl', function() {
      var scope, ctrl;

      beforeEach(module('hz.dashboard.launch-instance'));

      beforeEach(inject(function($controller) {
        scope = {
          model: {
            newInstanceSpec: {},
          }
        };

        ctrl = $controller('LaunchInstanceConfigurationCtrl', {
          $scope: scope
        });
      }));

      it('contains its own labels', function() {
        expect(ctrl.label).toBeDefined();
        expect(Object.keys(ctrl.label).length).toBeGreaterThan(0);
      });

      it('has correct disk configuration options', function() {
        expect(ctrl.diskConfigOptions).toBeDefined();
        expect(ctrl.diskConfigOptions.length).toBe(2);
        var vals = ctrl.diskConfigOptions.map(function(x) { return x.value; });
        expect(vals).toContain('AUTO');
        expect(vals).toContain('MANUAL');
      });

      it('defaults the disk configuration to "AUTO"', function() {
        expect(scope.model.newInstanceSpec.disk_config).toBe('AUTO');
      });

      it('defaults the config_drive configuration to false', function() {
        expect(scope.model.newInstanceSpec.config_drive).toBe(false);
      });

      it('defaults the user_data configuration to ""', function() {
        expect(scope.model.newInstanceSpec.user_data).toBe('');
      });

    });

    describe('LaunchInstanceConfigurationHelpCtrl', function() {
      var ctrl;

      beforeEach(module('hz.dashboard.launch-instance'));

      beforeEach(inject(function($controller) {
        ctrl = $controller('LaunchInstanceConfigurationHelpCtrl');
      }));

      it('defines the title', function() {
        expect(ctrl.title).toBeDefined();
      });

      it('has help paragraphs', function() {
        expect(ctrl.paragraphs).toBeDefined();
        expect(ctrl.paragraphs.length).toBeGreaterThan(0);
      });
    });

  });

})();

