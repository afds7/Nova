type NovaLogoProps = {
  className?: string;
};

/** Recorta a área transparente da arte com proporções, evitando cortes em qualquer viewport. */
export default function NovaLogo({ className = '' }: NovaLogoProps) {
  return (
    <div className={`relative aspect-[425/168] w-56 shrink-0 overflow-hidden sm:w-72 ${className}`}>
      <img
        src="/logo-nova.png"
        alt="Logo NOVA Hub"
        width={650}
        height={366}
        className="absolute left-[-109.4%] top-[-72.7%] h-auto w-[321.2%] max-w-none"
      />
    </div>
  );
}
