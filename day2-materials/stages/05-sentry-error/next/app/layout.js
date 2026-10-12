import "./globals.css";

export const metadata = {
  title: "메시지 보관함",
  description: "Next.js와 Flask로 메시지 저장하기",
};

export default function RootLayout({ children }) {
  return <html lang="ko"><body>{children}</body></html>;
}
