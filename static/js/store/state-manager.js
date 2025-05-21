/**
 * State Manager - Global state yönetimi
 */
export class StateManager {
    constructor() {
        this.state = {};
    }

    /**
     * State'e veri ekle veya güncelle
     */
    set(key, value) {
        if (typeof key === 'object') {
            this.state = { ...this.state, ...key };
        } else {
            this.state[key] = value;
        }
    }

    /**
     * State'ten veri oku
     */
    get(key) {
        return key ? this.state[key] : this.state;
    }
}
