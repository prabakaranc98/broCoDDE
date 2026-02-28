/** @type {import('next').NextConfig} */
const nextConfig = {
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    },
    experimental: {
        allowedDevOrigins: ["192.168.1.182", "localhost:3000"],
    },
};

module.exports = nextConfig;
