--
-- PostgreSQL database dump
--

\restrict USmWJV6e0vDqHouOC6H2lzqsi0VnMl4CbSQ0YE8fYrZusjB1IZiAMQfcKihDnsv

-- Dumped from database version 17.7 (Debian 17.7-3.pgdg13+1)
-- Dumped by pg_dump version 17.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admins (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.admins OWNER TO postgres;

--
-- Name: admins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.admins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admins_id_seq OWNER TO postgres;

--
-- Name: admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.admins_id_seq OWNED BY public.admins.id;


--
-- Name: radios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.radios (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(500) NOT NULL,
    description text,
    genre character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true
);


ALTER TABLE public.radios OWNER TO postgres;

--
-- Name: radios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.radios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.radios_id_seq OWNER TO postgres;

--
-- Name: radios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.radios_id_seq OWNED BY public.radios.id;


--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_sessions (
    sid character varying NOT NULL,
    sess json NOT NULL,
    expire timestamp(6) without time zone NOT NULL
);


ALTER TABLE public.user_sessions OWNER TO postgres;

--
-- Name: admins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins ALTER COLUMN id SET DEFAULT nextval('public.admins_id_seq'::regclass);


--
-- Name: radios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radios ALTER COLUMN id SET DEFAULT nextval('public.radios_id_seq'::regclass);


--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admins (id, username, password_hash, created_at) FROM stdin;
1	admin	$2a$10$ozyc2ZzMuDVjQVVQor/jGeWnMsYQQHJQWK04APFfjsR3TraPN7GUK	2025-12-04 17:23:52.682642
\.


--
-- Data for Name: radios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.radios (id, name, url, description, genre, created_at, is_active) FROM stdin;
1	Superloustic	https://radio6.pro-fhi.net/live/SUPERLOUSTIC	\N		2025-12-04 17:35:34.50692	t
2	Génération Dorothée	https://stream.votreradiosurlenet.eu/generationdorothee.mp3	\N		2025-12-04 18:35:49.832575	t
4	Nostalgie-Les Tubes 80 N1	https://streaming.nrjaudio.fm/ouo6im7nfibk	\N		2025-12-04 21:41:44.185601	t
8	Top 80 Radio	https://securestreams6.autopo.st:2321/;	\N		2025-12-04 21:47:43.768207	t
11	Chansons Oubliées Où Presque	https://manager7.streamradio.fr:2850/stream	\N		2025-12-04 21:55:25.621939	t
12	Made In 80	https://listen.radioking.com/radio/260719/stream/305509	\N		2025-12-04 21:56:56.129199	t
13	Chante France- 80s	https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3	\N		2025-12-04 21:58:51.061666	t
16	Générikds	https://www.radioking.com/play/generikids	\N		2025-12-06 14:37:22.611005	t
18	Supernana	https://radiosurle.net:8765/showsupernana	\N		2025-12-06 16:15:55.653504	t
19	Radio Gérard	https://radiosurle.net:8765/radiogerard	\N		2025-12-06 16:21:58.686871	t
20	RTL	http://streaming.radio.rtl.fr/rtl-1-44-128	\N		2025-12-06 19:15:02.583028	t
21	Radio Comercial	https://stream-icy.bauermedia.pt/comercial.mp3	\N		2025-12-06 21:41:59.871603	t
22	Mega Hits	https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC.aac	\N		2025-12-06 21:43:56.921467	t
23	Bide Et Musique	https://relay1.bide-et-musique.com:9300/bm.mp3	\N		2025-12-10 15:37:26.8835	t
25	Nostalgie-Les 80 Plus Grand Tubes	https://streaming.nrjaudio.fm/oug7oerb92oc	\N		2025-12-14 15:16:30	t
26	100% 80 Radio	https://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3	\N		2025-12-19 15:58:39.242913	t
27	Flash 80	https://manager7.streamradio.fr:1985/stream	\N		2025-12-19 16:03:34.488582	t
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_sessions (sid, sess, expire) FROM stdin;
A5OBoX9eZBnjuPSwoJ_uVE3hUjUMNf9r	{"cookie":{"originalMaxAge":604800000,"expires":"2025-12-21T15:15:52.490Z","secure":false,"httpOnly":true,"path":"/"},"user":{"id":1,"username":"admin"}}	2025-12-21 15:16:31
m0Y8UqxzQS5DLseondbRKtcDpdMJRkZa	{"cookie":{"originalMaxAge":604800000,"expires":"2025-12-17T10:57:38.996Z","secure":false,"httpOnly":true,"path":"/"},"user":{"id":1,"username":"admin"}}	2025-12-21 09:21:54
NBADRUP4gmm56x3LJBNyOBngK4P_MQeY	{"cookie":{"originalMaxAge":604800000,"expires":"2025-12-20T23:30:42.521Z","secure":false,"httpOnly":true,"path":"/"},"user":{"id":1,"username":"admin"}}	2025-12-26 17:00:14
\.


--
-- Name: admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admins_id_seq', 1, true);


--
-- Name: radios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.radios_id_seq', 27, true);


--
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (id);


--
-- Name: admins admins_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_username_key UNIQUE (username);


--
-- Name: radios radios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radios
    ADD CONSTRAINT radios_pkey PRIMARY KEY (id);


--
-- Name: radios radios_url_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radios
    ADD CONSTRAINT radios_url_key UNIQUE (url);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (sid);


--
-- PostgreSQL database dump complete
--

\unrestrict USmWJV6e0vDqHouOC6H2lzqsi0VnMl4CbSQ0YE8fYrZusjB1IZiAMQfcKihDnsv

