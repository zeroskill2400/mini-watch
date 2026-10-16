const nextConfig = {
  async rewrites() {
    // 로컬 확인용. Docker의 /api는 기존 게이트웨이가 전달한다.
    if (!process.env.LOCAL_MONITOR_API) return [];
    return [{ source: "/api/:path*", destination: process.env.LOCAL_MONITOR_API + "/api/:path*" }];
  },
};
export default nextConfig;
