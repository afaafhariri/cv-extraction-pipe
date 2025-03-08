import Image from "next/image";
function Footer() {
  return (
    <footer className="bg-[var(--background)] text-[var(--foreground)] px-8 py-5 flex justify-end items-center">
      <p className="text-sm mr-2">
        made by <span className="font-bold">Afaaf Hariri</span>
      </p>
      <a
        href="https://github.com/afaafhariri"
        target="_blank"
        rel="noreferrer"
        className="relative w-12 h-12"
      >
        <Image
          src="/profile.jpeg"
          alt="GitHub"
          fill
          className="rounded-full object-cover"
        />
      </a>
    </footer>
  );
}
export default Footer;
