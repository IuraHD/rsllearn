// Constants for the application
// Hardcoded data has been removed in favor of dynamic data from the backend.

export const APP_NAME = "RSLlingo";
export const API_URL = import.meta.env.VITE_API_URL || '/api';

export const DEFAULT_AVATAR = "/assets/default-avatar.png";

export const LEVELS = [
    { level: 1, xp: 0, title: "Începător" },
    { level: 2, xp: 1000, title: "Ucenic" },
    { level: 3, xp: 2500, title: "Explorator" },
    { level: 4, xp: 5000, title: "Cunoscător" },
    { level: 5, xp: 10000, title: "Expert" },
];
