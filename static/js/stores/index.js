/**
 * Stores Index
 *
 * Tüm Alpine.js store'larını içerir ve Alpine'a kaydeder
 * @module stores
 */

import themeStore from './theme';
import notificationStore from './notification';

/**
 * Tüm store'ları bir arada tutan obje
 */
export const stores = {
    theme: themeStore,
    notification: notificationStore
};

/**
 * Alpine.js yüklü ise store'ları kaydeder
 * @param {Object} Alpine - Alpine.js nesnesi
 */
export function registerStores(Alpine) {
    if (!Alpine) {
        console.error('Alpine.js not found, stores not registered');
        return;
    }

    // Store'ları Alpine'a kaydet
    Alpine.store('theme', themeStore);
    Alpine.store('notification', notificationStore);

    console.info('Alpine.js stores registered successfully');
}

export default {
    stores,
    registerStores
};
