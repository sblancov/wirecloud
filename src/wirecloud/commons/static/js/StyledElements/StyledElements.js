/*
 *     Copyright (c) 2008-2015 CoNWeT Lab., Universidad Politécnica de Madrid
 *
 *     This file is part of Wirecloud Platform.
 *
 *     Wirecloud Platform is free software: you can redistribute it and/or
 *     modify it under the terms of the GNU Affero General Public License as
 *     published by the Free Software Foundation, either version 3 of the
 *     License, or (at your option) any later version.
 *
 *     Wirecloud is distributed in the hope that it will be useful, but WITHOUT
 *     ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 *     FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
 *     License for more details.
 *
 *     You should have received a copy of the GNU Affero General Public License
 *     along with Wirecloud Platform.  If not, see
 *     <http://www.gnu.org/licenses/>.
 *
 */

/* global CSSPrimitiveValue, StyledElements */


(function (se, utils) {

    "use strict";

    // ==================================================================================
    // CLASS DEFINITION
    // ==================================================================================

    /**
     * Create a new instance of class StyledElement.
     *
     * @constructor
     * @param {String[]} events [description]
     */
    se.StyledElement = utils.defineClass({

        constructor: function StyledElement(events) {
            this.wrapperElement = null;
            this.parentElement = null;

            Object.defineProperties(this, {

                enabled: {
                    get: function get() {
                        return !this.hasClassName('disabled');
                    },
                    set: function set(value) {
                        value = !!value; // Convert into boolean
                        if (this.enabled !== value) {
                            this.toggleClassName('disabled', !value)
                                ._onenabled(value);
                        }
                    }
                },

                hidden: {
                    get: function get() {
                        return this.hasClassName('hidden');
                    },
                    set: function set(value) {
                        this.toggleClassName('hidden', value)
                            ._onhidden(value);
                    }
                }

            });

            if (!Array.isArray(events)) {
                events = [];
            }
            this.mixinClass(0, ['hide', 'show'].concat(events));
        },

        mixins: [se.ObjectWithEvents],

        members: {

            /**
             * @protected
             */
            _onenabled: function _onenabled(enabled) {
                // This member can be implemented by subclass.
            },

            /**
             * @protected
             */
            _onhidden: function _onhidden(hidden) {
                // This member can be implemented by subclass.
            },

            /**
             * Adds one or more classes to this StyledElement.
             *
             * @param {String|String[]} classList
             *      One or more space-separated classes to be added to the
             *      wrapperElement.
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            addClassName: function addClassName(classList) {

                if (!Array.isArray(classList)) {
                    classList = classList == null ? "" : classList.toString().trim();
                    if (classList === "") {
                        return;
                    }
                    classList = classList.split(/\s+/);
                }

                classList.forEach(add_individual_class, this);

                return this;
            },

            /**
             * Inserts this StyledElement to the end of the targetElement
             * @version 0.6
             *
             * @param {StyledElement|HTMLElement} targetElement
             *      An element to insert the wrapperElement.
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            appendTo: function appendTo(targetElement) {
                return this.insertInto(targetElement);
            },

            /**
             * Disables this StyledElement
             * @version 0.5
             *
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            disable: function disable() {
                this.enabled = false;

                return this;
            },

            /**
             * Enables this StyledElement
             * @version 0.6
             *
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            enable: function enable() {
                this.enabled = true;

                return this;
            },

            /**
             * Gets the root element for this StyledElement
             * @version 0.6
             *
             * @returns {HTMLElement}
             *      If the wrapperElement is not instance of HTMLElement, the member
             *      throws TypeError exception.
             */
            get: function get() {
                return this.wrapperElement;
            },

            /**
             * Displays this StyledElement
             * @version 0.6
             *
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            hide: function hide() {

                if (!this.hidden) {
                    this.hidden = true;
                    this.events.hide.trigger(this);
                }

                return this;
            },

            /**
             * Gets the parent of this StyledElement
             * @version 0.6
             *
             * @returns {HTMLElement}
             *      The parent element of the wrapperElement.
             */
            parent: function parent() {

                if (this.parentElement != null) {
                    return this.parentElement.get();
                }

                return this.get().parentElement;
            },

            /**
             * Insert the wrapperElement to the beginning of the targetElement children.
             * @param {StyledElement|HTMLElement} targetElement
             *      An element to insert the wrapperElement.
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            prependTo: function prependTo(targetElement) {
                if (targetElement instanceof se.StyledElement) {
                    return targetElement.prependChild(this);
                } else {
                    return this.insertInto(targetElement, targetElement.firstChild);
                }
            },

            /**
             * Remove this StyledElement from the DOM.
             * @version 0.6
             *
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            remove: function remove() {

                if (this.parentElement != null) {
                    this.parentElement.remove(this);
                } else {
                    if (this.get().parentElement != null) {
                        this.get().parentElement.removeChild(this.get());
                    }
                }

                return this;
            },

            /**
             * Replaces CSS classes with others.
             * @version 0.6
             *
             * @param {String|String[]} removeList
             *      classes to remove
             * @param {String|String[]} addList
             *      classes to add
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            replaceClassName: function replaceClassName(removeList, addList) {
                this.removeClassName(removeList);
                this.addClassName(addList);

                return this;
            },

            /**
             * Display the wrapperElement.
             * @version 0.6
             *
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            show: function show() {

                if (this.hidden) {
                    this.hidden = false;
                    this.events.show.trigger(this);
                }

                return this;
            },

            /**
             * Get the value of a computed style property or set one or more CSS
             * properties for the wrapperElement.
             * @version 0.6
             *
             * @param {String|Object.<String, *>} properties
             *      A CSS property name or an object of property-value pairs.
             * @param {String|Number} [value]
             *      Optional. A value to set for the property.
             * @returns {StyledElement|String}
             *      The instance on which the member is called or the CSS property value.
             */
            style: function style(properties, value) {

                if (arguments.length === 1) {
                    if (typeof properties === 'string') {
                        return this.get().style[properties];
                    }

                    for (var name in properties) {
                        this.get().style[name] = properties[name];
                    }
                } else {
                    this.get().style[properties] = value != null ? value : "";
                }

                return this;
            },

            /**
             * Add or remove one or more classes from this StyledElement,
             * depending on either the class's presence. Additionaly, you can
             * use the state parameter for indicating if you want to add or
             * delete them.
             * @version 0.6
             *
             * @param {String} classList
             *      One or more space-separated classes to be toggled from the
             *      wrapperElement.
             * @param {Boolean} [state]
             *      A boolean value to determine if the class should be added or removed.
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            toggleClassName: function toggleClassName(classList, state) {
                classList = typeof classList !== 'string' ? "" : classList.trim();

                if (classList.length) {
                    if (typeof state !== 'boolean') {
                        classList.split(/\s+/).forEach(function (className) {
                            if (this.get().classList.contains(className)) {
                                this.get().classList.remove(className);
                            } else {
                                this.get().classList.add(className);
                            }
                        }, this);
                    } else {
                        var method = state ? "add" : "remove";

                        classList.split(/\s+/).forEach(function (className) {
                            this.get().classList[method](className);
                        }, this);
                    }
                }

                return this;
            },

            _getUsableHeight: function _getUsableHeight() {
                var parentElement = this.wrapperElement.parentNode;
                if (!StyledElements.Utils.XML.isElement(parentElement)) {
                    return null;
                }

                var parentStyle = document.defaultView.getComputedStyle(parentElement, null);
                if (parentStyle.getPropertyCSSValue('display') == null) {
                    return null;
                }
                var containerStyle = document.defaultView.getComputedStyle(this.wrapperElement, null);

                var height = parentElement.offsetHeight -
                             parentStyle.getPropertyCSSValue('padding-top').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             parentStyle.getPropertyCSSValue('padding-bottom').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             containerStyle.getPropertyCSSValue('padding-top').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             containerStyle.getPropertyCSSValue('padding-bottom').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             containerStyle.getPropertyCSSValue('border-top-width').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             containerStyle.getPropertyCSSValue('border-bottom-width').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             containerStyle.getPropertyCSSValue('margin-top').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                             containerStyle.getPropertyCSSValue('margin-bottom').getFloatValue(CSSPrimitiveValue.CSS_PX);

                return height;
            },

            _getUsableWidth: function _getUsableWidth() {
                var parentElement = this.wrapperElement.parentNode;
                if (!StyledElements.Utils.XML.isElement(parentElement)) {
                    return null;
                }

                var parentStyle = document.defaultView.getComputedStyle(parentElement, null);
                var containerStyle = document.defaultView.getComputedStyle(this.wrapperElement, null);

                var width = parentElement.offsetWidth -
                            parentStyle.getPropertyCSSValue('padding-left').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                            parentStyle.getPropertyCSSValue('padding-right').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                            containerStyle.getPropertyCSSValue('padding-left').getFloatValue(CSSPrimitiveValue.CSS_PX) -
                            containerStyle.getPropertyCSSValue('padding-right').getFloatValue(CSSPrimitiveValue.CSS_PX);

                return width;
            },

            getBoundingClientRect: function getBoundingClientRect() {
                return this.wrapperElement.getBoundingClientRect();
            },

            /**
             * Check if this StyledElement is assigned a class.
             *
             * @param {String} className
             *      A class name to search for.
             * @returns {Boolean}
             *      If the class is assigned to the wrapperElement, even if other classes
             *      also are.
             */
            hasClassName: function hasClassName(className) {
                className = className == null ? "" : className.toString().trim();

                return this.get().classList.contains(className);
            },

            /**
             * Inserts this StyledElement at the end of the given element. If
             * the refElement parameter is used, then this StyledElement will be
             * inserted before refElement.
             *
             * @param {Container|HTMLElement} element
             *      An element where this StyledElement will be inserted.
             * @param {StyledElement|HTMLElement} [refElement]
             *      Optional. An element after which newElement is going to be
             *      inserted.
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            insertInto: function insertInto(element, refElement) {
                if (element instanceof StyledElements.StyledElement) {
                    element = element.wrapperElement;
                }

                if (refElement instanceof StyledElements.StyledElement) {
                    refElement = refElement.wrapperElement;
                }

                if (refElement) {
                    element.insertBefore(this.wrapperElement, refElement);
                } else {
                    element.appendChild(this.wrapperElement);
                }

                return this;
            },

            /**
             * Removes multiple or all classes from this StyledElement
             * @version 0.6
             *
             * @param {String|String[]} [classList]
             *      Optional. One or more space-separated classes to be removed from this
             *      StyledElement. If you pass an empty string as the classList parameter,
             *      all classes will be removed.
             * @returns {StyledElement}
             *      The instance on which the member is called.
             */
            removeClassName: function removeClassName(classList) {
                if (!Array.isArray(classList)) {
                    classList = classList == null ? "" : classList.toString().trim();
                    if (classList === "") {
                        this.get().removeAttribute('class');
                    }
                    classList = classList.split(/\s+/);
                }

                classList.forEach(remove_individual_class, this);

                return this;
            },

            /**
             * Repaints this StyledElement.
             *
             * @param {Boolean} temporal `true` if the repaint should be
             * handled as temporal repaint that will be followed, in a short
             * period of time, by more calls to this method. In that case, the
             * sequence should end with a call to this method using `false`
             * for the temporal parameter. `false` by default.
             */
            repaint: function repaint(temporal) {return this;},

            /**
             * @deprecated since version 0.6
             * @see enabled property
             */
            setDisabled: function setDisabled(disable) {
                if (disable) {
                    return this.disable();
                } else {
                    return this.enable();
                }
            }

        }

    });

    // ==================================================================================
    // PRIVATE MEMBERS
    // ==================================================================================

    var add_individual_class = function (className) {
        this.get().classList.add(className);
    };

    var remove_individual_class = function (className) {
        this.get().classList.remove(className);
    };

})(StyledElements, StyledElements.Utils);
