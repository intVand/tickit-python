-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1:3308
-- Tiempo de generación: 22-05-2026 a las 19:51:11
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `tickit_db`
--

-- Se crea la base de datos solo si no existe previamente en el servidor.

CREATE DATABASE IF NOT EXISTS `tickit_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Se selecciona la base de datos activa para la ejecución de las siguientes tablas

USE `tickit_db`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `asignaciones_tickets`
--

CREATE TABLE `asignaciones_tickets` (
  `id` int(11) NOT NULL,
  `id_ticket` int(11) NOT NULL,
  `id_tecnico` int(11) NOT NULL,
  `fecha_asignacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `asignaciones_tickets`
--

INSERT INTO `asignaciones_tickets` (`id`, `id_ticket`, `id_tecnico`, `fecha_asignacion`) VALUES
(6, 1, 1, '2026-05-11 15:29:36'),
(8, 9, 1, '2026-05-22 19:44:20'),
(9, 8, 1, '2026-05-22 19:44:24'),
(10, 7, 1, '2026-05-22 19:44:28');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `departamentos`
--

CREATE TABLE `departamentos` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `edificio` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `departamentos`
--

INSERT INTO `departamentos` (`id`, `nombre`, `edificio`) VALUES
(2, 'Soporte IT - Software', 'Edificio Principal'),
(3, 'Redes y Telecomunicaciones', 'Edificio Principal'),
(4, 'Mantenimiento de Instalaciones', 'Nave 2'),
(5, 'Recursos Humanos', 'Oficinas Centrales'),
(11, 'Sin asignar', 'Sistema Interno'),
(13, 'Soporte IT - Hardware', 'Edificio Principal');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

CREATE TABLE `roles` (
  `id` int(11) NOT NULL,
  `nombre_rol` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `roles`
--

INSERT INTO `roles` (`id`, `nombre_rol`) VALUES
(1, 'admin'),
(2, 'usuario');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tickets`
--

CREATE TABLE `tickets` (
  `id` int(11) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `descripcion` text NOT NULL,
  `estado` enum('Pendiente','En Progreso','Resuelto') DEFAULT 'Pendiente',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_resolucion` datetime DEFAULT NULL,
  `id_usuario` int(11) NOT NULL,
  `id_departamento` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `tickets`
--

INSERT INTO `tickets` (`id`, `titulo`, `descripcion`, `estado`, `fecha_creacion`, `fecha_resolucion`, `id_usuario`, `id_departamento`) VALUES
(1, 'No enciende el PC.', 'Hola, desde está mañana que el ordenador no enciende, ayer por la tarde lo deje actualizando.', 'Resuelto', '2026-05-07 16:45:09', '2026-05-11 15:29:57', 1, 13),
(4, 'La puerta del almacén no abre.', 'Hola, llevamos ya varias semanas con problemas con la puerta del almacén, avise ya a recursos humanos, pero no hay contestación.', 'Pendiente', '2026-05-22 18:54:48', NULL, 3, 4),
(7, 'Windows funciona lento.', 'Hola, hoy por alguna razón Windows me funciona más lento de lo normal, se podría pasar alguien de IT para revisarlo?', 'En Progreso', '2026-05-22 19:39:33', NULL, 1, 2),
(8, 'La impresora red no funciona.', 'Perdonar, pero llevo ya varios meses teniendo que ir personalmente a imprimir los documentos, podéis arreglar pronto la conexión de la impresora?', 'Resuelto', '2026-05-22 19:41:02', '2026-05-22 19:44:24', 3, 3),
(9, 'Vacaciones.', 'Buenos días, es posible que pueda librar por vacaciones la semana del 15 de junio?', 'En Progreso', '2026-05-22 19:42:21', NULL, 3, 5),
(10, 'Teclado desgastado.', 'Podría alguien de IT traerme un teclado nuevo, llevo usando el mismo desde que entre a la empresa, y está ya muy desgastado.', 'Pendiente', '2026-05-22 19:44:02', NULL, 3, 13);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `contrasenya` varchar(255) NOT NULL,
  `id_rol` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre`, `email`, `contrasenya`, `id_rol`) VALUES
(1, 'Iván', 'ivan@tickit.com', 'scrypt:32768:8:1$FDsV7ti2ilqK10xE$101965c2eecdbb9ab603ff61bade01564663c8922a7ac78a7aa446d5fefb814f8b49b08b9a6eeb9d4762240bed6e8eed8d1aec94f28b6930502f89248c7dc91c', 1),
(3, 'Jose', 'jose@tickit.com', 'scrypt:32768:8:1$zbKNUWgIOtxZAkOf$ecd0b92047e2c3a5889fd61768dc86967f02878dfe37b6698c2ca3c799722369135b6f01f0e2092b010fa97b3e7f483814691a278d9ced5c0bec18d8ba1263c2', 2);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `asignaciones_tickets`
--
ALTER TABLE `asignaciones_tickets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_ticket` (`id_ticket`),
  ADD KEY `id_tecnico` (`id_tecnico`);

--
-- Indices de la tabla `departamentos`
--
ALTER TABLE `departamentos`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre_rol` (`nombre_rol`);

--
-- Indices de la tabla `tickets`
--
ALTER TABLE `tickets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_usuario` (`id_usuario`),
  ADD KEY `id_departamento` (`id_departamento`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `id_rol` (`id_rol`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `asignaciones_tickets`
--
ALTER TABLE `asignaciones_tickets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT de la tabla `departamentos`
--
ALTER TABLE `departamentos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `tickets`
--
ALTER TABLE `tickets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `asignaciones_tickets`
--
ALTER TABLE `asignaciones_tickets`
  ADD CONSTRAINT `asignaciones_tickets_ibfk_1` FOREIGN KEY (`id_ticket`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `asignaciones_tickets_ibfk_2` FOREIGN KEY (`id_tecnico`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `tickets`
--
ALTER TABLE `tickets`
  ADD CONSTRAINT `tickets_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `tickets_ibfk_2` FOREIGN KEY (`id_departamento`) REFERENCES `departamentos` (`id`);

--
-- Filtros para la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
