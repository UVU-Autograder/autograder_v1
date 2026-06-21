interface NavbarProps {
  role: "admin" | "student";
}

export default function Navbar ({role} : NavbarProps) {
    return (
    <div>
        <h1>Admin</h1>
    </div>
    )
}